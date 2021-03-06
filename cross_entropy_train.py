#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr  8 16:21:17 2019

@author: yuming
"""
import sys
sys.path.append('/home/yuming/projects/learn-with-noisy-labels/nets')

import torch
import torch.nn as nn
import torch.optim as optim
import copy
import time
import numpy as np
from squeezenet import squeezenet1_1
from matplotlib import pyplot as plt
from dataloader import load_data

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
save_name = "models/model_squeezenet_20190409.pth"
num_epochs = 9

def train_model(model, trainloader, testloader, num_epochs=9):
    since = time.time()
    model.to(device)
    
    val_acc_history = []
    
    best_model_wts = copy.deepcopy(model.state_dict())
    best_acc = 0.0

    # loss function and optimizer
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.SGD(model.parameters(), lr=1e-3, momentum=0.9, weight_decay=1e-5)
    scheduler = optim.lr_scheduler.MultiStepLR(optimizer, [3, 6])

    for epoch in range(num_epochs):
        print('Epoch {}/{}'.format(epoch, num_epochs - 1))
        
        scheduler.step()
        running_loss = 0.0
        model.train()

        for i, data in enumerate(trainloader, 0):
            # get the inputs
            inputs, labels, name = data
            inputs, labels = inputs.to(device), labels.to(device)
            
            # zero the parameter gradients
            optimizer.zero_grad()
            
            # forward + backward + optimize
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            running_loss += loss.item()
            
        print('loss: %.5f' % (running_loss / (i+1)))
        
        # evaluation
        running_loss = 0.0
        model.eval()
        correct = 0
        total = 0
        for data in testloader:
            images, labels, _ = data
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += torch.sum(predicted == labels)
            
        # statistics
        eval_acc = correct.double() / total
        val_acc_history.append(eval_acc)
        
        # deep copy the best model
        if eval_acc > best_acc:
            best_acc = eval_acc
            best_model_wts = copy.deepcopy(model.state_dict())
            torch.save(best_model_wts, save_name)
                
        print(eval_acc)
    
    torch.save(model.state_dict(), "models/model_last.pth")
    time_elapsed = time.time() - since
    print('Training complete in {:.0f}m {:.0f}s'.format(time_elapsed // 60, time_elapsed % 60))
    print('Best val Acc: {:4f}'.format(best_acc))
    
    # load best model weights
    model.load_state_dict(best_model_wts)
    return model, val_acc_history

def plot(hist):
    plt.title("Validation Accuracy vs. Number of Training Epochs")
    plt.xlabel("Training Epochs")
    plt.ylabel("Validation Accuracy")
    plt.plot(range(1, num_epochs+1), hist)
    plt.ylim(0, 1.)
    plt.xticks(np.arange(0, len(hist) + 1, 50))
    plt.show()

if __name__ == '__main__':
    train_source = '/data/yuming/image_qa/data/fuzzy_train_crop.txt'
    test_source = '/data/yuming/image_qa/data/fuzzy_test_crop.txt'
    trainloader, testloader = load_data(train_source, test_source)
    model = squeezenet1_1(num_classes=4)
    model, hist = train_model(model, trainloader, testloader, num_epochs)
    plot(hist)
