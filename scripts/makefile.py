from pathlib import Path

SUFFIX = "abl"


def float_to_scientific(values):
    return [f"{v:.1E}".replace(".", "-") for v in values]


def generate_banner(group_names: list[str]):
    b = ""
    b += "##########################################################################\n"
    b += f"# make all -f Makefile.{SUFFIX}\n"
    for i, group in enumerate(group_names):
        b += f"# GROUP{i}: make {group} -f Makefile.{SUFFIX}\n"
    b += "##########################################################################\n"
    return b


def generate_group_banner(group_name: str = "GROUP"):
    b = ""
    b += "##########################################################################\n"
    b += f"# {group_name}\n"
    b += "##########################################################################\n"
    b += "\n"
    return b


def generate_make_command(template_generator, value, group_name, prefix):
    task_name = f"{group_name}__{prefix}"
    make_command = f"{task_name}:"
    template = template_generator.format(
        task_name=task_name, value=value, group_name=group_name
    )
    template = make_command + template
    return task_name, template


def build_group(template_generator, values, prefixs, group_name: str = "GROUP"):
    templates = []
    task_names = []
    for value, prefix in zip(values, prefixs):
        task_name, template = generate_make_command(
            template_generator=template_generator,
            value=value,
            group_name=group_name,
            prefix=prefix,
        )
        t = "\n\t".join(
            [li.strip() for li in template.split("\n") if li and li.strip()]
        )
        task_names.append(task_name)
        templates.append(t)

    temp = generate_group_banner(group_name)
    tasks = " ".join(task_names)
    temp += f"\n{group_name}: {tasks}\n\n"
    temp += "\n\n".join(templates)
    temp += "\n"

    return temp, group_name, tasks


def build_makefile(groups):
    templates, group_names, task_names = [], [], []
    for group in groups:
        temp, names, task = group
        templates.append(temp)
        group_names.append(names)
        task_names.append(task)
    g = generate_banner(group_names)
    g += "\n"
    tasks = " ".join(task_names)
    g += f".PHONY: all {tasks}\n"
    g += f"all: {tasks}\n\n"
    g += "\n\n".join(templates)
    g += "\n\n"
    return g


def main():
    groups = []

    data_dir = Path("/home/borth/GuidedResearch/data/dphm_kinect")
    # dataset_names = sorted(list(p.name for p in data_dir.iterdir()))

    values = [
        "christoph_eyeblink",
        # "christoph_fastalk",
        "christoph_mouthmove",
        # "christoph_rotatemouth",
        # "christoph_smile",
    ]
    prefixs = values

    # group_name = "prepare_dataset"
    # template_generator = """
    # python scripts/prepare_dataset.py \\
    # logger.group={group_name} \\
    # logger.name={task_name} \\
    # logger.tags=[{group_name},{task_name}] \\
    # task_name={task_name} \\
    # data.dataset_name={value} \\
    # """
    # groups.append(build_group(template_generator, values, prefixs, group_name))

    group_name = "optimize1"
    template_generator = """
    python scripts/optimize.py \\
    logger.group={group_name} \\
    logger.name={task_name} \\
    logger.tags=[{group_name},{task_name}] \\
    task_name={task_name} \\
    data.dataset_name={value} \\
    store_params=true \\
    residuals.chain.shape_regularization.weight=7e-03 \\
	residuals.chain.expression_regularization.weight=1e-03 \\
	residuals.chain.neck_regularization.weight=5e-02 \\
    """
    groups.append(build_group(template_generator, values, prefixs, group_name))

    group_name = "optimize2"
    template_generator = """
    python scripts/optimize.py \\
    logger.group={group_name} \\
    logger.name={task_name} \\
    logger.tags=[{group_name},{task_name}] \\
    task_name={task_name} \\
    data.dataset_name={value} \\
    store_params=true \\
    residuals.chain.shape_regularization.weight=6e-03 \\
	residuals.chain.expression_regularization.weight=1e-03 \\
	residuals.chain.neck_regularization.weight=5e-02 \\
    """
    groups.append(build_group(template_generator, values, prefixs, group_name))

    group_name = "optimize3"
    template_generator = """
    python scripts/optimize.py \\
    logger.group={group_name} \\
    logger.name={task_name} \\
    logger.tags=[{group_name},{task_name}] \\
    task_name={task_name} \\
    data.dataset_name={value} \\
    store_params=true \\
    residuals.chain.shape_regularization.weight=5e-03 \\
	residuals.chain.expression_regularization.weight=1e-03 \\
	residuals.chain.neck_regularization.weight=5e-02 \\
    """
    groups.append(build_group(template_generator, values, prefixs, group_name))

    with open(f"Makefile.{SUFFIX}", "w") as f:
        f.write(build_makefile(groups))


if __name__ == "__main__":
    main()
