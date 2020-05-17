import torch as t
import torch.nn.functional as F
from torch import nn

from lib.conv import conv, kernel
from lib.util import img
from lib.util.config import Config
from lib.util.inspect import show_tensor
from lib.util.logger_factory import LoggerFactory


class PerceptionStep:
    def __init__(self, filters, out_channels_per_filter):
        self.__filters = filters
        self.__out_channels_per_filter = out_channels_per_filter

    def apply(self, input):
        outputs = []
        for filter_ in self.__filters:
            weights = conv.weights(filter_, self.__out_channels_per_filter)
            show_tensor('weights', weights)

            input_batch = input[None, :]
            show_tensor('input_batch', input_batch)

            output = F.conv2d(input_batch, weights, stride=1, padding=1)
            show_tensor('output', output)

            outputs.append(output)

        return t.cat(outputs, 0)


class CellGrowthModel(nn.Module):
    def __init__(self, perception_step):
        super(CellGrowthModel, self).__init__()
        self.__perception_step = perception_step

    def forward(self, input):
        perception = self.__perception_step.apply(input)
        return perception


def load_img_as_input_tensor(file_path):
    img_tensor = img.load_as_tensor(file_path)

    width, height = img_tensor.size()[1], img_tensor.size()[2]

    # alpha_channel = t.zeros((1, width, height))
    # rand_channel = t.rand((1, width, height))

    # extra_channels = t.stack(alpha_channel + rand_channel * 12, 0)

    # input_tensor = t.stack([img_tensor, extra_channels], 0)

    normalized_tensor = img.normalize_tensor(img_tensor, from_channel=0, to_channel=3)
    return normalized_tensor


IN_CHANNELS = 3

# ---------------------------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------------------------
if __name__ == "__main__":
    config = Config('./config.yaml')
    logger_factory = LoggerFactory(config['logger']).create()

    input_tensor = load_img_as_input_tensor('data/dragon.png')
    # img.show(input_tensor)

    # Create model
    perception_step = PerceptionStep(
        filters=[
            conv.repeated_kernel_filter(kernel.SOLVER_X, IN_CHANNELS),
            conv.repeated_kernel_filter(kernel.SOLVER_Y, IN_CHANNELS),
            conv.repeated_kernel_filter(kernel.IDENTITY, IN_CHANNELS)
        ],
        out_channels_per_filter=IN_CHANNELS
    )
    model = CellGrowthModel(perception_step)

    output = model.forward(input_tensor)

    img.show(output[0])
    img.show(output[1])
    img.show(output[2])
