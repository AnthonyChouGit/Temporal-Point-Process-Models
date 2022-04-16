from data_utils.data import prepare_dataloader
from models.model import TPP
from eval_utils.eval import evalNll, evalPred
import torch
from torch.optim import Adam
from torch.optim.lr_scheduler import StepLR
from datetime import datetime
from tqdm import tqdm
import math

class Tester:
    def __init__(self, config, data_dir, device, model_name, max_len=None, max_epoch=400, 
    batch_size=32, eval_batch_size=128, pred_batch_size=64, init_lr=5e-4, patience=70, threshold=1e-4, lr_step=30,
     step_gamma=0.5, reload_step=10, display_step=30) -> None:
        self.data_dir = data_dir
        self.device = device
        self.model_name=model_name
        self.max_len=max_len
        self.batch_size=batch_size
        self.eval_batch_size = eval_batch_size
        self.init_lr = init_lr
        self.patience=patience
        self.lr_step=lr_step
        self.step_gamma=step_gamma
        self.reload_step=reload_step
        self.display_step=display_step
        self.max_epoch = max_epoch
        self.threshold = threshold
        self.config = config

        self.train_data, _,  self.dev_data, self.test_data, self.pred_loader, self.num_types = prepare_dataloader(data_dir, batch_size, eval_batch_size, pred_batch_size, max_len)
        config['num_types'] = self.num_types
        self.model = TPP(config).to(device)

    def train(self):
        optimizer = Adam(self.model.parameters(), lr=self.init_lr)
        scheduler = StepLR(optimizer, self.lr_step, gamma=self.step_gamma)
        now = datetime.now().strftime("%D %H:%M:%S")
        with open(f'{self.model_name}.txt', 'a') as f:
            f.write(f'{now}\n')
            f.write(f'{self.config}\n')
        best_loss = math.inf
        impatient = 0
        for epoch in tqdm(range(self.max_epoch)):
            for ind, batch in enumerate(self.train_data):
                event_time, _, event_type = batch
                optimizer.zero_grad()
                loss = self.model.compute_loss(event_type, event_time)
                loss.backward()
                optimizer.step()
            scheduler.step()
            with torch.no_grad():
                dev_loss = evalNll(self.model, self.dev_data)
                if (best_loss - dev_loss) < self.threshold: 
                    impatient += 1
                    if dev_loss < best_loss:
                        best_loss = dev_loss
                        torch.save(self.model.state_dict(), f'state_dicts/{self.model_name}')
                else:
                    best_loss = dev_loss
                    torch.save(self.model.state_dict(), f'state_dicts/{self.model_name}')
                    impatient = 0
                if (epoch+1)%self.display_step==0:
                    with open(f'{self.model_name}.txt', 'a') as f:
                        f.write(f'epoch {epoch+1} finished, best_loss={best_loss}.\n')
                    print(f'epoch {epoch+1} finished, best_loss={best_loss}.')
            if impatient >= self.patience:
                break
            if (epoch+1)%self.reload_step==0:
                self.loadModel()
                # self.model.load_state_dict(torch.load(f'state_dicts/{self.model_name}'))
        self.loadModel()
        # torch
        # torch.save(self.model.state_dict(), f'state_dicts/{self.model_name}')
    
    def loadModel(self):
        self.model.load_state_dict(torch.load(f'state_dicts/{self.model_name}'))

    def testNll(self):
        self.loadModel()
        with torch.no_grad():
            test_loss = evalNll(self.model, self.test_data)
        print(f'All done. Test_loss={test_loss}.')
        with open(f'{self.model_name}.txt', 'a') as f:
            f.write(f'All done. Test_loss={test_loss}.\n')
        # TODO: test NLL and prediction error

    def testPred(self):
        self.loadModel()
        with torch.no_grad():
            type_acc, dt_error = evalPred(self.model, self.pred_loader)
        print(f'All done. ACC={type_acc}, RMSE={dt_error}.')
        with open(f'{self.model_name}.txt', 'a') as f:
            f.write(f'All done. ACC={type_acc}, RMSE={dt_error}.')
