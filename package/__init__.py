import torch
import torchvision
import torchvision.transforms as transforms
import matplotlib.pyplot as plt
import numpy as np
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import argparse
import sys
from PIL import Image
import os
from sklearn.metrics import classification_report

class Net(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv2d(3, 6, 5)
        self.pool = nn.MaxPool2d(2, 2)
        self.conv2 = nn.Conv2d(6, 16, 5)
        self.fc1 = nn.Linear(16 * 5 * 5, 120)
        self.fc2 = nn.Linear(120, 84)
        self.fc3 = nn.Linear(84, 10)

    def forward(self, x):
        x = self.pool(F.relu(self.conv1(x)))
        x = self.pool(F.relu(self.conv2(x)))
        x = torch.flatten(x, 1) # flatten all dimensions except batch
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = self.fc3(x)
        return x
    
def imshow(img):                    #outside def main() maybe?
        img = img / 2 + 0.5     # unnormalize
        npimg = img.numpy()
        plt.imshow(np.transpose(npimg, (1, 2, 0)))
        plt.show()

def main():
    parser = argparse.ArgumentParser(description='CIFAR10 Trainer/Tester')
    parser.add_argument('--train', action='store_true', help='Train the model')
    parser.add_argument('--test', type=str, help='Path to an image to test')
    parser.add_argument('--dataset', type=str, default='cifar10', help='CIFAR10 or custom dataset')
    args = parser.parse_args()
    

    transform = transforms.Compose(
    [transforms.ToTensor(),
     transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))])
    
    classes = ('plane', 'car', 'bird', 'cat',
            'deer', 'dog', 'frog', 'horse', 'ship', 'truck')
    
    PATH = './cifar_net.pth'


    if args.train:
        if args.dataset == 'cifar10':
            batch_size = 4

            trainset = torchvision.datasets.CIFAR10(root='./data', train=True,
                                                    download=True, transform=transform)
            trainloader = torch.utils.data.DataLoader(trainset, batch_size=batch_size,
                                                    shuffle=True, num_workers=2)

            testset = torchvision.datasets.CIFAR10(root='./data', train=False,
                                                download=True, transform=transform)
            testloader = torch.utils.data.DataLoader(testset, batch_size=batch_size,
                                                    shuffle=False, num_workers=2)
        elif args.dataset == 'custom':
            batch_size = 4
            data = './data/custom'
            
            train = os.path.join(data, 'train')
            test = os.path.join(data, 'test')

            trainset = torchvision.datasets.ImageFolder(train, transform=transform)
            trainloader = torch.utils.data.DataLoader(trainset, batch_size=batch_size,
                                                    shuffle=True, num_workers=2)

            testset = torchvision.datasets.ImageFolder(test, transform=transform)
            testloader = torch.utils.data.DataLoader(testset, batch_size=batch_size,
                                                    shuffle=False, num_workers=2)

            classes = trainset.classes  # automatically get class names from folders

        

        # get some random training images
        dataiter = iter(trainloader)
        images, labels = next(dataiter)

        # show images
        imshow(torchvision.utils.make_grid(images))
        # print labels
        print(' '.join(f'{classes[labels[j]]:5s}' for j in range(batch_size)))

        net = Net()

        criterion = nn.CrossEntropyLoss()
        optimizer = optim.SGD(net.parameters(), lr=0.001, momentum=0.9)

        for epoch in range(2):  # loop over the dataset multiple times

            running_loss = 0.0
            for i, data in enumerate(trainloader, 0):
                # get the inputs; data is a list of [inputs, labels]
                inputs, labels = data

                # zero the parameter gradients
                optimizer.zero_grad()

                # forward + backward + optimize
                outputs = net(inputs)
                loss = criterion(outputs, labels)
                loss.backward()
                optimizer.step()

                # print statistics
                running_loss += loss.item()
                if i % 2000 == 1999:    # print every 2000 mini-batches
                    print(f'[{epoch + 1}, {i + 1:5d}] loss: {running_loss / 2000:.3f}')
                    running_loss = 0.0

        print('Finished Training')

        
        torch.save(net.state_dict(), PATH)

        dataiter = iter(testloader)
        images, labels = next(dataiter)

        # print images
        imshow(torchvision.utils.make_grid(images))
        print('GroundTruth: ', ' '.join(f'{classes[labels[j]]:5s}' for j in range(4)))

        net = Net()
        net.load_state_dict(torch.load(PATH, weights_only=True))

        outputs = net(images)
        _, predicted = torch.max(outputs, 1)

        print('Predicted: ', ' '.join(f'{classes[predicted[j]]:5s}'
                              for j in range(4)))
        
        correct = 0
        total = 0
        # since we're not training, we don't need to calculate the gradients for our outputs
        with torch.no_grad():
            for data in testloader:
                images, labels = data
                # calculate outputs by running images through the network
                outputs = net(images)
                # the class with the highest energy is what we choose as prediction
                _, predicted = torch.max(outputs, 1)
                total += labels.size(0)
                correct += (predicted == labels).sum().item()

        print(f'Accuracy of the network on the 10000 test images: {100 * correct // total} %')

        # prepare to count predictions for each class
        correct_pred = {classname: 0 for classname in classes}
        total_pred = {classname: 0 for classname in classes}

        all_preds = []
        all_labels = []

        # again no gradients needed
        with torch.no_grad():
            for data in testloader:
                images, labels = data
                outputs = net(images)
                _, predictions = torch.max(outputs, 1)

                all_preds.extend(predictions.cpu().numpy())
                all_labels.extend(labels.cpu().numpy())

                # collect the correct predictions for each class
                for label, prediction in zip(labels, predictions):
                    if label == prediction:
                        correct_pred[classes[label]] += 1
                    total_pred[classes[label]] += 1


        # print accuracy for each class
        for classname, correct_count in correct_pred.items():
            accuracy = 100 * float(correct_count) / total_pred[classname]
            print(f'Accuracy for class: {classname:5s} is {accuracy:.1f} %')

        report = classification_report(all_labels, all_preds, target_names=classes, zero_division=0)
        
        with open("classification_report.txt", "w") as f:
            f.write(report)
    
    elif args.test:
        if not os.path.exists(PATH):
            print(f"Error: Trained model not found at '{PATH}'. Run--train first.")
            sys.exit(1)

        net = Net()
        net.load_state_dict(torch.load(PATH))
        net.eval()

        try:
            image = Image.open(args.test).convert('RGB')
        except Exception as e:
            print(f"Error loading image: {e}")
            sys.exit(1)

        image = transform(image).unsqueeze(0)

        with torch.no_grad():
            outputs = net(image)
            _, predicted = torch.max(outputs, 1)

        print(f'Predicted class: {classes[predicted.item()]}')

    else:
        print("Usage:\n  --train: Train CIFAR10 classifier\n  --train --dataset custom: Train custom dataset\n  --test <image_path>: Classify image")
        sys.exit(1)

        