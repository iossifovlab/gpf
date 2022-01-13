import yaml
import os
import pprint
import logging

logger = logging.getLogger(__name__)


def adjust_instance_id(config, adjustments):
    vars = config["vars"]
    vars["instance_id"] = adjustments["instance_id"]
    print(f"replacing instance id with {adjustments['instance_id']}")


def adjust_impala(config, adjustments):
    storage = config["storage"]
    genotype_impala = storage["genotype_impala"]
    impala = genotype_impala["impala"]
    hosts = impala["hosts"]
    impala["hosts"] = adjustments["impala_hosts"]

    print(f"replacing impala hosts: {hosts} with {impala['hosts']}")


def adjust_hdfs(config, adjustments):
    storage = config["storage"]
    genotype_impala = storage["genotype_impala"]
    hdfs = genotype_impala["hdfs"]
    host = hdfs["host"]
    hdfs["host"] = adjustments["hdfs_host"]

    print(f"replacing impala hosts: {host} with {hdfs['host']}")

    if "rsync" in genotype_impala:
        del genotype_impala["rsync"]


def adjust_available_studies(config, adjustments):
    gpfjs = config["gpfjs"]

    print(
        f"replacing available studies with: "
        f"{adjustments.get('available_studies')}")

    if adjustments.get("available_studies") is None:
        if "selected_genotype_data" in gpfjs:
            del gpfjs["selected_genotype_data"]
    else:
        gpfjs["selected_genotype_data"] = adjustments["available_studies"]


def main(adjustments):
    filename = os.path.join(os.environ.get("DAE_DB_DIR"), "gpf_instance.yaml")
    if not os.path.exists(filename):
        logger.error(f"can't find DAE_DB_DIR instance config: {filename}")
        return

    with open(filename) as infile:
        config = yaml.safe_load(infile.read())
    
    pprint.pprint(config)

    adjust_instance_id(config, adjustments)
    adjust_impala(config, adjustments)
    adjust_hdfs(config, adjustments)
    adjust_available_studies(config, adjustments)

    pprint.pprint(config)

    with open(filename, "w") as outfile:
        outfile.write(yaml.safe_dump(config))