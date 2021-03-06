import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.nn import init
##model unet
from torchsummary import summary


class double_conv(nn.Module):
    def __init__(self,in_ch,out_ch):
        super(double_conv,self).__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(in_ch,out_ch,3,padding = 1),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace = True),
            nn.Conv2d(out_ch,out_ch,3,padding = 1),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace = True)
        )
        self.conv.apply(self.init_weights)
    def forward(self,x):
        x = self.conv(x)
        return x

    @staticmethod
    def init_weights(m):
        if type(m) == nn.Conv2d:
            init.xavier_normal_(m.weight)
            init.constant_(m.bias, 0)

    
class inconv(nn.Module):
    def __init__(self,in_ch,out_ch):
        super(inconv,self).__init__()
        self.conv = double_conv(in_ch,out_ch)
    
    def forward(self,x):
        x = self.conv(x)
        return x
    
    
class down(nn.Module):
    def __init__(self,in_ch,out_ch):
        super(down,self).__init__()
        self.mpconv = nn.Sequential(
            nn.MaxPool2d(2),
            double_conv(in_ch,out_ch)
        )
    def forward(self,x):
        x = self.mpconv(x)
        return x 


class up(nn.Module):
    def __init__(self,in_ch,out_ch,bilinear = True):
        super(up,self).__init__()
        if bilinear:
            self.up = nn.Upsample(scale_factor = 2,mode = 'bilinear',align_corners = True)
        else :
            self.up = nn.ConvTransposed2d(in_ch//2,in_ch//2,2,stride = 2)
        self.conv = double_conv(in_ch,out_ch)
        self.up.apply(self.init_weights)
    
    def forward(self,x1,x2):
        x1 = self.up(x1)
        diffY = x1.size()[2] - x2.size()[2]  # 得到图像x2与x1的H的差值，56-64=-8
        diffX = x1.size()[3] - x2.size()[3]  # 得到图像x2与x1的W差值，56-64=-8
        x2 = F.pad(x2, (diffX // 2, diffX - diffX//2,
                        diffY // 2, diffY - diffY//2))
        x = torch.cat([x2, x1], dim=1)
        x = self.conv(x)
        return x

    @staticmethod
    def init_weights(m):
        if type(m) == nn.Conv2d:
            init.xavier_normal_(m.weight)
            init.constant_(m.bias, 0)

        
class outconv(nn.Module):
    def __init__(self, in_ch, out_ch):
        super(outconv, self).__init__()
        self.conv = nn.Conv2d(in_ch, out_ch, 1)

    def forward(self, x):
        x = self.conv(x)
        return x  


import torch.nn.functional as F

# from .unet_parts import *

class UNet(nn.Module):
    def __init__(self, n_channels, n_classes): #图片的通道数，1为灰度图像，3为彩色图像
        super(UNet, self).__init__()
        self.inc = inconv(n_channels, 64) #假设输入通道数n_channels为3，输出通道数为64
        self.down1 = down(64, 128)
        self.down2 = down(128, 256)
        self.down3 = down(256, 512)
        self.down4 = down(512, 512)
        self.up1 = up(1024, 256)
        self.up2 = up(512, 128)
        self.up3 = up(256, 64)
        self.up4 = up(128, 64)
        self.outc = outconv(64, n_classes)

    def forward(self, x):
        x1 = self.inc(x)
        x2 = self.down1(x1)
        x3 = self.down2(x2)
        x4 = self.down3(x3)
        x5 = self.down4(x4)
        x = self.up1(x5, x4)
        x = self.up2(x, x3)
        x = self.up3(x, x2)
        x = self.up4(x, x1)
        x = self.outc(x)
        return x


if __name__ == '__main__':
    net = UNet(3,6).cuda()
    summary(net,(3,512,512))