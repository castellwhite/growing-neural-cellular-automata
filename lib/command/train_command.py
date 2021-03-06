import torch.optim as optim
from torch.nn import MSELoss

from lib.command.command import Command
from lib.model.callback.log_metrics import LogMetrics
from lib.model.callback.plot_metrics import PlotMetrics
from lib.model.callback.plot_output import PlotOutput
from lib.model.callback.save_weights import SaveWeights
from lib.model.cell_growth.cell_growth_model_builder import build_model_from
from lib.model.cell_growth.data_tensor import DataTensor
from lib.script_utils import get_target


class TrainCommand(Command):
    def exec(self, cfg, args):
        model = build_model_from(cfg)
        model.load(cfg['model.weights.path'])

        target = get_target(cfg, args.config_name())
        initial = DataTensor.initial(target)

        callbacks = [
            SaveWeights(
                path=cfg['model.weights.path'],
                every=cfg['model.weights.save_every']
            ),
            LogMetrics()
        ]

        if args.show_output():
            callbacks.append(
                PlotOutput(
                    every=cfg['model.preview.every'],
                    window_size=(cfg['model.preview.width'] * 2, cfg['model.preview.height']),
                    target=target
                )
            )

        if args.show_loss_graph():
            callbacks.append(PlotMetrics(reset_every=cfg['model.train.metrics.reset_every']))

        optimizer = optim.Adam(
            model.parameters(),
            lr=cfg['model.train.lr']
        )

        scheduler = optim.lr_scheduler.StepLR(
            optimizer=optimizer,
            step_size=cfg['model.train.scheduler.step_size'],
            gamma=cfg['model.train.scheduler.gamma']
        )

        model.train(
            epochs=cfg['model.train.epochs'],
            steps=(cfg['model.train.steps.min'], cfg['model.train.steps.max']),
            initial=initial,
            target=target,
            optimizer=optimizer,
            scheduler=scheduler,
            loss_fn=MSELoss(reduction='sum'),
            callbacks=callbacks
        )
