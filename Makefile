####################################################################################
# Different Levenberg Marquardt Settings
# make dynamic_lm dynamic_lm_levenberg static_lm_gn static_lm_gd
####################################################################################

levenberg_marquardt:
	python scripts/optimize.py \
	task_name=levenberg_marquardt \
	loss=regularization \
	optimizer=levenberg_marquardt \
	joint_trainer.max_iters=100 \
	joint_trainer.max_optims=50 \
	model.init_sigma=0.0005 \
	sequential_trainer=null

dynamic_lm_baseline:
	python scripts/optimize.py \
	task_name=dynamic_lm_baseline \
	optimizer=levenberg_marquardt \
	joint_trainer.init_idxs=[0] \

dynamic_lm_levenberg:
	python scripts/optimize.py \
	task_name=dynamic_lm_levenberg \
	optimizer=levenberg_marquardt \
	optimizer.optimizer_params.only_levenberg=True \

# dynamic_lm_linesearch:
# 	python scripts/optimize.py \
# 	task_name=dynamic_lm_linesearch \
# 	optimizer=levenberg_marquardt \
# 	optimizer.optimizer_params.line_search_fn=ternary_search \

static_lm_gn:
	python scripts/optimize.py \
	task_name=static_lm_gn \
	optimizer=levenberg_marquardt \
	optimizer.optimizer_params.mode=static \
	optimizer.optimizer_params.damping_factor=0.0 \

static_lm_gd:
	python scripts/optimize.py \
	task_name=static_lm_gd \
	optimizer=levenberg_marquardt \
	optimizer.optimizer_params.mode=static \
	optimizer.optimizer_params.damping_factor=1.0 \

####################################################################################
# PCG vs Pytorch Levenberg Marquardt Settings
# make lm_pcg_5_no_jacobi lm_pcg_1 lm_pcg_5 lm_pcg_20 lm_pytorch 
####################################################################################

lm_pytorch:
	python scripts/optimize.py \
	task_name=lm_pytorch \
	optimizer=levenberg_marquardt \
	optimizer.optimizer_params.lin_solver=pytorch \


lm_pcg_1:
	python scripts/optimize.py \
	task_name=lm_pcg_1 \
	optimizer=levenberg_marquardt \
	optimizer.optimizer_params.lin_solver=pcg \
	optimizer.optimizer_params.pcg_steps=1 \


lm_pcg_5:
	python scripts/optimize.py \
	task_name=lm_pcg_5 \
	optimizer=levenberg_marquardt \
	optimizer.optimizer_params.lin_solver=pcg \
	optimizer.optimizer_params.pcg_steps=5 \

lm_pcg_5_no_jacobi:
	python scripts/optimize.py \
	task_name=lm_pcg_5_no_jacobi \
	optimizer=levenberg_marquardt \
	optimizer.optimizer_params.lin_solver=pcg \
	optimizer.optimizer_params.pcg_steps=5 \
	optimizer.optimizer_params.pcg_jacobi=False \

lm_levenberg:
	python scripts/optimize.py \
	task_name=lm_levenberg \
	optimizer=levenberg_marquardt \
	optimizer.optimizer_params.lin_solver=pcg \
	optimizer.optimizer_params.pcg_steps=5 \
	optimizer.optimizer_params.only_levenberg=True \

lm_pcg_20:
	python scripts/optimize.py \
	task_name=lm_pcg_20 \
	optimizer=levenberg_marquardt \
	optimizer.optimizer_params.lin_solver=pcg \
	optimizer.optimizer_params.pcg_steps=20 \

####################################################################################
# Different Loss Functions 
# make lm2d lm3d plane point symm reg
####################################################################################

lm2d:
	python scripts/optimize.py \
	task_name=lm2d \
	optimizer=levenberg_marquardt \
	loss=landmark2d \

lm3d:
	python scripts/optimize.py \
	task_name=lm3d \
	optimizer=levenberg_marquardt \
	loss=landmark3d \

plane:
	python scripts/optimize.py \
	task_name=plane \
	optimizer=levenberg_marquardt \
	loss=point2plane \

point:
	python scripts/optimize.py \
	task_name=point \
	optimizer=levenberg_marquardt \
	loss=point2point \

symm:
	python scripts/optimize.py \
	task_name=symm \
	optimizer=levenberg_marquardt \
	loss=symmetricICP \

reg:
	python scripts/optimize.py \
	task_name=reg \
	optimizer=levenberg_marquardt \
	loss=regularization \

# make dynamic_lm dynamic_lm_levenberg static_lm_gn static_lm_gd lm_pytorch lm_pcg_5_no_jacobi lm_pcg_1 lm_pcg_5 lm_pcg_20 lm2d lm3d plane point symm reg

####################################################################################
# LM One Iter vs Adam
####################################################################################

gauss_newton:
	python scripts/optimize.py \
	task_name=gauss_newton \
	optimizer=gauss_newton \
	optimizer.optimizer_params.pcg_steps=1 \
	optimizer.optimizer_params.pcg_jacobi=False \
	loss=point2plane \
	joint_trainer.final_video=False \
	joint_trainer.init_idxs=[0] \
	joint_trainer.max_iters=1 \
	joint_trainer.max_optims=1 \
	joint_trainer.optimizer.milestones=[0] \
	joint_trainer.optimizer.params=[[global_pose,transl]] \
	joint_trainer.coarse2fine.milestones=[0] \
	joint_trainer.coarse2fine.scales=[8] \
	sequential_trainer=null \

lm_one_optim:
	python scripts/optimize.py \
	task_name=lm_one_optim \
	optimizer=levenberg_marquardt \
	joint_trainer.max_iters=150 \
	joint_trainer.max_optims=1 \
	joint_trainer.optimizer.milestones=[0,50,60] \
	joint_trainer.optimizer.params=[[global_pose,transl],[neck_pose,eye_pose],[shape_params,expression_params]] \
	sequential_trainer.max_iters=10 \
	sequential_trainer.max_optims=1 \
	sequential_trainer.optimizer.milestones=[0] \
	sequential_trainer.optimizer.params=[[global_pose,transl,neck_pose,eye_pose,expression_params]] \


adam_one_optim:
	python scripts/optimize.py \
	task_name=adam_one_optim \
	optimizer=adam \
	joint_trainer.max_iters=500 \
	joint_trainer.max_optims=1 \
	joint_trainer.optimizer.milestones=[0,150,200] \
	joint_trainer.optimizer.params=[[global_pose,transl],[neck_pose,eye_pose],[shape_params,expression_params]] \
	sequential_trainer.max_iters=100 \
	sequential_trainer.max_optims=1 \
	sequential_trainer.optimizer.milestones=[0] \
	sequential_trainer.optimizer.params=[[global_pose,transl,neck_pose,eye_pose,expression_params]] \



####################################################################################
# Others
####################################################################################


adam:
	python scripts/optimize.py \
	tags=["adam"] \
	trainer.optimizer=adam \
	trainer.copy_optimizer_state=True \
	trainer.optimizer_params={lr:1e-02} \
	joint_trainer.max_iters=30 \
	joint_trainer.max_optims=100 \
	joint_trainer.optimizer.milestones=[0,7,10] \
	joint_trainer.optimizer.params=[[global_pose,transl],[neck_pose,eye_pose],[shape_params,expression_params]] \
	sequential_trainer.max_iters=20 \
	sequential_trainer.max_optims=50 \
	sequential_trainer.optimizer.milestones=[0] \
	sequential_trainer.optimizer.params=[[global_pose,transl,neck_pose,eye_pose,expression_params]] \

adam_low_lr:
	python scripts/optimize.py \
	tags=["adam_low_lr"] \
	data.batch_size=10 \
	model.optimize_frames=10 \
	trainer.max_iters=20 \
	trainer.max_optims=200 \
	trainer.optimizer=adam \
	trainer.copy_optimizer_state=False \
	trainer.coarse2fine.milestones=[0] \
	trainer.coarse2fine.scales=[8] \
	trainer.optimizer.milestones=[0,5,7] \
	trainer.optimizer.params=[["global_pose","transl"],["neck_pose"],["shape_params","expression_params"]] \
	trainer.optimizer.lr=[[1e-03,1e-03],[1e-03],[1e-03,1e-03]]

adam_copy:
	python scripts/optimize.py \
	tags=["adam_copy"] \
	data.batch_size=10 \
	model.optimize_frames=10 \
	trainer.max_iters=20 \
	trainer.max_optims=200 \
	trainer.optimizer=adam \
	trainer.copy_optimizer_state=True \
	trainer.coarse2fine.milestones=[0] \
	trainer.coarse2fine.scales=[8] \
	trainer.optimizer.milestones=[0,5,7] \
	trainer.optimizer.params=[["global_pose","transl"],["neck_pose"],["shape_params","expression_params"]] \
	trainer.optimizer.lr=[[1e-02,1e-02],[1e-02],[1e-02,1e-02]]

adam_copy_high_lr:
	python scripts/optimize.py \
	tags=["adam_copy_high_lr"] \
	data.batch_size=10 \
	model.optimize_frames=10 \
	trainer.max_iters=20 \
	trainer.max_optims=200 \
	trainer.optimizer=adam \
	trainer.copy_optimizer_state=True \
	trainer.coarse2fine.milestones=[0] \
	trainer.coarse2fine.scales=[8] \
	trainer.optimizer.milestones=[0,5,7] \
	trainer.optimizer.params=[["global_pose","transl"],["neck_pose"],["shape_params","expression_params"]] \
	trainer.optimizer.lr=[[1,1],[1],[1,1]]

ternary_linesearch:
	python scripts/optimize.py \
	tags=["ternary_linesearch"] \
	data.batch_size=10 \
	model.optimize_frames=10 \
	trainer.max_iters=20 \
	trainer.max_optims=50 \
	trainer.optimizer=ternary_linesearch \
	trainer.copy_optimizer_state=False \
	trainer.coarse2fine.milestones=[0] \
	trainer.coarse2fine.scales=[8] \
	trainer.optimizer.milestones=[0,5,7] \
	trainer.optimizer.params=[["global_pose","transl"],["neck_pose"],["shape_params","expression_params"]] \
	trainer.optimizer.lr=[[0,0],[0],[0,0]]

gradient_decent_momentum_copy:
	python scripts/optimize.py \
	tags=["gradient_decent_momentum_copy"] \
	data.batch_size=10 \
	model.optimize_frames=10 \
	trainer.max_iters=20 \
	trainer.max_optims=50 \
	trainer.optimizer=gradient_decent_momentum \
	trainer.copy_optimizer_state=True \
	trainer.coarse2fine.milestones=[0] \
	trainer.coarse2fine.scales=[8] \
	trainer.optimizer.milestones=[0,5,7] \
	trainer.optimizer.params=[["global_pose","transl"],["neck_pose"],["shape_params","expression_params"]] \
	trainer.optimizer.lr=[[10,10],[10],[10,10]]

gradient_decent_momentum:
	python scripts/optimize.py \
	tags=["gradient_decent_momentum"] \
	data.batch_size=10 \
	model.optimize_frames=10 \
	trainer.max_iters=20 \
	trainer.max_optims=50 \
	trainer.optimizer=gradient_decent_momentum \
	trainer.copy_optimizer_state=False \
	trainer.coarse2fine.milestones=[0] \
	trainer.coarse2fine.scales=[8] \
	trainer.optimizer.milestones=[0,5,7] \
	trainer.optimizer.params=[["global_pose","transl"],["neck_pose"],["shape_params","expression_params"]] \
	trainer.optimizer.lr=[[10,10],[10],[10,10]]

gradient_decent:
	python scripts/optimize.py \
	tags=["gradient_decent"] \
	data.batch_size=10 \
	model.optimize_frames=10 \
	trainer.max_iters=20 \
	trainer.max_optims=50 \
	trainer.optimizer=gradient_decent \
	trainer.copy_optimizer_state=False \
	trainer.coarse2fine.milestones=[0] \
	trainer.coarse2fine.scales=[8] \
	trainer.optimizer.milestones=[0,5,7] \
	trainer.optimizer.params=[["global_pose","transl"],["neck_pose"],["shape_params","expression_params"]] \
	trainer.optimizer.lr=[[10,10],[10],[10,10]]

create_video:
	python scripts/create_video.py +framerate=20 +video_dir="/home/borth/GuidedResearch/logs/optimize/runs/2024-06-07_12-49-31/render_normal" +video_path="temp/render_normal.mp4"
	python scripts/create_video.py +framerate=20 +video_dir="/home/borth/GuidedResearch/logs/optimize/runs/2024-06-07_12-49-31/batch_color" +video_path="temp/batch_color.mp4"
	python scripts/create_video.py +framerate=20 +video_dir="/home/borth/GuidedResearch/logs/optimize/runs/2024-06-07_12-49-31/error_point_to_plane" +video_path="temp/error_point_to_plane.mp4"
	python scripts/create_video.py +framerate=20 +video_dir="/home/borth/GuidedResearch/logs/optimize/runs/2024-06-07_12-49-31/render_merged" +video_path="temp/render_merged.mp4"