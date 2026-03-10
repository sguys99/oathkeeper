# import os
# import random

# import numpy as np
# import torch


# def set_random_seed(
#     random_seed: int = 42,
#     use_torch: bool = False,
# ) -> None:
#     """
#     여러 라이브러리에서 재현성을 위해 전역 랜덤 시드를 설정한다.

#     Args:
#         random_seed (int): 설정할 시드 값
#         use_torch (bool): PyTorch 시드 설정 여부
#     """
#     os.environ["PYTHONHASHSEED"] = str(random_seed)
#     random.seed(random_seed)
#     np.random.seed(random_seed)

#     if use_torch:
#         torch.manual_seed(random_seed)
#         torch.cuda.manual_seed(random_seed)
#         torch.cuda.manual_seed_all(random_seed)
#         torch.backends.cudnn.deterministic = True
#         torch.backends.cudnn.benchmark = False
