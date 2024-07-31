def float_to_scientific(values):
    return [f"{v:.1E}".replace(".", "-") for v in values]


def generate_banner(group_names: list[str]):
    b = ""
    b += "##########################################################################\n"
    b += "# make all -f Makefile.abl\n"
    for i, group in enumerate(group_names):
        b += f"# GROUP{i}: make {group} -f Makefile.abl\n"
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

    values = [
        1e-06,
        3e-06,
        5e-06,
        7e-06,
        9e-06,
        1e-05,
        3e-05,
        5e-05,
        7e-05,
        9e-05,
        1e-04,
        3e-04,
        5e-04,
        7e-04,
        9e-04,
        1e-03,
        3e-03,
        5e-03,
        8e-03,
        7e-03,
        9e-03,
    ]
    prefixs = float_to_scientific(values)

    group_name = "pcg_full_scheduler1_lr"
    template_generator = """
    python scripts/pcg_training.py \\
    logger.group={group_name} \\
    logger.name={task_name} \\
    logger.tags=[{group_name},{task_name}] \\
    task_name={task_name} \\
    model.optimizer.lr={value} \\
    model.max_iter=1 \\
    model.loss._target_=lib.optimizer.pcg.L1SolutionLoss \\
    model.condition_net._target_=lib.optimizer.pcg.DenseConditionNet \\
    model.condition_net.num_layers=2 \\
    +model.scheduler._target_=torch.optim.lr_scheduler.ExponentialLR \\
    +model.scheduler._partial_=True \\
    +model.scheduler.gamma=0.99 \\
    data=linsys_pose_full \\
    data.batch_size=1024 \\
    trainer.max_epochs=500 \\
    """
    groups.append(build_group(template_generator, values, prefixs, group_name))

    group_name = "pcg_full_scheduler2_lr"
    template_generator = """
    python scripts/pcg_training.py \\
    logger.group={group_name} \\
    logger.name={task_name} \\
    logger.tags=[{group_name},{task_name}] \\
    task_name={task_name} \\
    model.optimizer.lr={value} \\
    model.max_iter=2 \\
    model.loss._target_=lib.optimizer.pcg.L1SolutionLoss \\
    model.condition_net._target_=lib.optimizer.pcg.DenseConditionNet \\
    model.condition_net.num_layers=2 \\
    +model.scheduler._target_=torch.optim.lr_scheduler.ExponentialLR \\
    +model.scheduler._partial_=True \\
    +model.scheduler.gamma=0.99 \\
    data=linsys_pose_full \\
    data.batch_size=1024 \\
    trainer.max_epochs=500 \\
    """
    groups.append(build_group(template_generator, values, prefixs, group_name))

    group_name = "pcg_full_scheduler3_lr"
    template_generator = """
    python scripts/pcg_training.py \\
    logger.group={group_name} \\
    logger.name={task_name} \\
    logger.tags=[{group_name},{task_name}] \\
    task_name={task_name} \\
    model.optimizer.lr={value} \\
    model.max_iter=3 \\
    model.loss._target_=lib.optimizer.pcg.L1SolutionLoss \\
    model.condition_net._target_=lib.optimizer.pcg.DenseConditionNet \\
    model.condition_net.num_layers=2 \\
    +model.scheduler._target_=torch.optim.lr_scheduler.ExponentialLR \\
    +model.scheduler._partial_=True \\
    +model.scheduler.gamma=0.99 \\
    data=linsys_pose_full \\
    data.batch_size=1024 \\
    trainer.max_epochs=500 \\
    """
    groups.append(build_group(template_generator, values, prefixs, group_name))

    group_name = "pcg_full_scheduler4_lr"
    template_generator = """
    python scripts/pcg_training.py \\
    logger.group={group_name} \\
    logger.name={task_name} \\
    logger.tags=[{group_name},{task_name}] \\
    task_name={task_name} \\
    model.optimizer.lr={value} \\
    model.max_iter=4 \\
    model.loss._target_=lib.optimizer.pcg.L1SolutionLoss \\
    model.condition_net._target_=lib.optimizer.pcg.DenseConditionNet \\
    model.condition_net.num_layers=2 \\
    +model.scheduler._target_=torch.optim.lr_scheduler.ExponentialLR \\
    +model.scheduler._partial_=True \\
    +model.scheduler.gamma=0.99 \\
    data=linsys_pose_full \\
    data.batch_size=1024 \\
    trainer.max_epochs=500 \\
    """
    groups.append(build_group(template_generator, values, prefixs, group_name))

    group_name = "pcg_full_scheduler5_lr"
    template_generator = """
    python scripts/pcg_training.py \\
    logger.group={group_name} \\
    logger.name={task_name} \\
    logger.tags=[{group_name},{task_name}] \\
    task_name={task_name} \\
    model.optimizer.lr={value} \\
    model.max_iter=5 \\
    model.loss._target_=lib.optimizer.pcg.L1SolutionLoss \\
    model.condition_net._target_=lib.optimizer.pcg.DenseConditionNet \\
    model.condition_net.num_layers=2 \\
    +model.scheduler._target_=torch.optim.lr_scheduler.ExponentialLR \\
    +model.scheduler._partial_=True \\
    +model.scheduler.gamma=0.99 \\
    data=linsys_pose_full \\
    data.batch_size=1024 \\
    trainer.max_epochs=500 \\
    """
    groups.append(build_group(template_generator, values, prefixs, group_name))

    group_name = "pcg_full_scheduler6_lr"
    template_generator = """
    python scripts/pcg_training.py \\
    logger.group={group_name} \\
    logger.name={task_name} \\
    logger.tags=[{group_name},{task_name}] \\
    task_name={task_name} \\
    model.optimizer.lr={value} \\
    model.max_iter=6 \\
    model.loss._target_=lib.optimizer.pcg.L1SolutionLoss \\
    model.condition_net._target_=lib.optimizer.pcg.DenseConditionNet \\
    model.condition_net.num_layers=2 \\
    +model.scheduler._target_=torch.optim.lr_scheduler.ExponentialLR \\
    +model.scheduler._partial_=True \\
    +model.scheduler.gamma=0.99 \\
    data=linsys_pose_full \\
    data.batch_size=1024 \\
    trainer.max_epochs=500 \\
    """
    groups.append(build_group(template_generator, values, prefixs, group_name))

    group_name = "pcg_full_scheduler7_lr"
    template_generator = """
    python scripts/pcg_training.py \\
    logger.group={group_name} \\
    logger.name={task_name} \\
    logger.tags=[{group_name},{task_name}] \\
    task_name={task_name} \\
    model.optimizer.lr={value} \\
    model.max_iter=7 \\
    model.loss._target_=lib.optimizer.pcg.L1SolutionLoss \\
    model.condition_net._target_=lib.optimizer.pcg.DenseConditionNet \\
    model.condition_net.num_layers=2 \\
    +model.scheduler._target_=torch.optim.lr_scheduler.ExponentialLR \\
    +model.scheduler._partial_=True \\
    +model.scheduler.gamma=0.99 \\
    data=linsys_pose_full \\
    data.batch_size=1024 \\
    trainer.max_epochs=500 \\
    """
    groups.append(build_group(template_generator, values, prefixs, group_name))

    group_name = "pcg_full_scheduler8_lr"
    template_generator = """
    python scripts/pcg_training.py \\
    logger.group={group_name} \\
    logger.name={task_name} \\
    logger.tags=[{group_name},{task_name}] \\
    task_name={task_name} \\
    model.optimizer.lr={value} \\
    model.max_iter=8 \\
    model.loss._target_=lib.optimizer.pcg.L1SolutionLoss \\
    model.condition_net._target_=lib.optimizer.pcg.DenseConditionNet \\
    model.condition_net.num_layers=2 \\
    +model.scheduler._target_=torch.optim.lr_scheduler.ExponentialLR \\
    +model.scheduler._partial_=True \\
    +model.scheduler.gamma=0.99 \\
    data=linsys_pose_full \\
    data.batch_size=1024 \\
    trainer.max_epochs=500 \\
    """
    groups.append(build_group(template_generator, values, prefixs, group_name))

    with open("Makefile.abl", "w") as f:
        f.write(build_makefile(groups))


if __name__ == "__main__":
    main()
