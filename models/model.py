import torch 
from torch import nn
from .nhp.model import NHP
from .conv_tpp.model import ConvTPP

class TPP(nn.Module):
    def __init__(self, config):
        super(TPP, self).__init__()
        num_types = config['num_types']
        embed_dim = config['embed_dim']
        # self.embed = nn.Embedding(num_types+2, embed_dim, padding_idx=0)
        self.num_types = num_types
        model_name = config['model']
        if model_name.lower() == 'nhp':
            self.model = NHP(config)
        elif model_name.lower() == 'conv-tpp':
            self.model = ConvTPP(config)
        else:
            raise NotImplementedError(f'{model_name} is not implemented.')
        self.register_buffer('device_indicator', torch.empty(0))

    def compute_loss(self, type_seq, time_seq):
        device = self.device_indicator.device
        type_seq, time_seq = processSeq(type_seq, time_seq, self.num_types+1)
        # type_seq = type_seq.to(device)
        # embed_seq = self.embed(type_seq)
        loss = self.model.compute_loss(type_seq, time_seq)
        return loss


    def predict(self, type_seq, time_seq):
        device = self.device_indicator.device
        type_seq, time_seq = processSeq(type_seq.unsqueeze(0), time_seq.unsqueeze(0), self.num_types+1)
        type_seq = type_seq.flatten()
        time_seq = time_seq.flatten()
        # type_seq = type_seq.to(device)
        # embed_seq = self.embed(type_seq)
        return self.model.predict(type_seq, time_seq)

def processSeq(type_seq, time_seq, sos_ind):
    device = type_seq.device
    batch_size = type_seq.shape[0]
    time_seq = time_seq - time_seq[:, 0].view(-1, 1)
    type_seq = torch.cat([torch.ones(batch_size, 1, device=device) * sos_ind, type_seq], dim=1).long()
    time_seq = torch.cat([torch.zeros(batch_size, 1, device=device), time_seq], dim=1)
    return type_seq, time_seq
