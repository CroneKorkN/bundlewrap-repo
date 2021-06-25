from pipes import quote

from bundlewrap.exceptions import BundleError
from bundlewrap.items import Item
from bundlewrap.utils.text import mark_for_translation as _


def create(node, path, options):
    option_list = []
    for option, value in sorted(options.items()):
        # We must exclude the 'mounted' property here because it's a
        # read-only "informational" property.
        if option != 'mounted' and value is not None:
            option_list.append("-o {}={}".format(quote(option), quote(value)))
    option_args = " ".join(option_list)

    node.run(
        "zfs create -p {} {}".format(
            option_args,
            quote(path),
        ),
        may_fail=True,
    )

    if options['mounted'] == 'no':
        set_option(node, path, 'mounted', 'no')


def does_exist(node, path):
    status_result = node.run(
        "zfs list {}".format(quote(path)),
        may_fail=True,
    )
    return status_result.return_code == 0


def get_option(node, path, option):
    cmd = "zfs get -Hp -o value {} {}".format(quote(option), quote(path))
    # We always expect this to succeed since we don't call this function
    # if we have already established that the dataset does not exist.
    status_result = node.run(cmd)
    return status_result.stdout.decode('utf-8').strip()

def set_option(node, path, option, value):
    if option == 'mounted':
        # 'mounted' is a read-only property that can not be altered by
        # 'set'. We need to call 'zfs mount tank/foo'.
        node.run(
            "zfs {} {}".format(
                "mount" if value == 'yes' else "unmount",
                quote(path),
            ),
            may_fail=True,
        )
    else:
        node.run(
            "zfs set {}={} {}".format(
                quote(option),
                quote(value),
                quote(path),
            ),
            may_fail=True,
        )


class ZFSDataset(Item):
    """
    Creates ZFS datasets and manages their options.
    """
    BUNDLE_ATTRIBUTE_NAME = "zfs_datasets"
    ITEM_ATTRIBUTES = {
        'atime': None,
        'acltype': None,
        'compression': None,
        'mountpoint': None,
        'quota': None,
        'recordsize': None,
        'dedup': None,
    }
    ITEM_TYPE_NAME = "zfs_dataset"

    def __repr__(self):
        return f"<ZFSDataset name:{self.name} {' '.join(f'{k}:{v}' for k,v in self.attributes.items())}>"

    def cdict(self):
        cdict = {}
        for option, value in self.attributes.items():
            if option == 'mountpoint' and value is None:
                value = "none"
            if value is not None:
                cdict[option] = value
        cdict['mounted'] = 'no' if cdict.get('mountpoint') in (None, "none") else 'yes'
        return cdict

    def fix(self, status):
        if status.must_be_created:
            create(self.node, self.name, status.cdict)
        else:
            for option in status.keys_to_fix:
                set_option(self.node, self.name, option, status.cdict[option])

    def get_auto_deps(self, items):
        pool = self.name.split("/")[0]
        pool_item = "zfs_pool:{}".format(pool)
        pool_item_found = False

        for item in items:
            if item.ITEM_TYPE_NAME == "zfs_pool" and item.name == pool:
                # Add dependency to the pool this dataset resides on.
                pool_item_found = True
                yield pool_item
            elif (
                item.ITEM_TYPE_NAME == "zfs_dataset" and
                self.name != item.name and
                self.name.startswith(item.name + "/")
            ):
                # Find all other datasets that are parents of this
                # dataset.
                # XXX Could be optimized by finding the "largest"
                # parent only.
                yield item.id

        if not pool_item_found:
            raise BundleError(_(
                "ZFS dataset {dataset} resides on pool {pool} but item "
                "{dep} does not exist"
            ).format(
                dataset=self.name,
                pool=pool,
                dep=pool_item,
            ))

    def sdict(self):
        if not does_exist(self.node, self.name):
            return None

        sdict = {}
        for option, value in self.attributes.items():
            sdict[option] = get_option(self.node, self.name, option)
        sdict['mounted'] = get_option(self.node, self.name, 'mounted')
        return sdict
