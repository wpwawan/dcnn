import numpy as np
import dataloader
import models
import logger
import torch
import tqdm
import os


def get_arguments():
    import argparse
    model_choices = ['dcnn','dcnn-relu','dcnn-leakyrelu','mlp']
    parser = argparse.ArgumentParser('Dynamic CNN in PyTorch')

    parser.add_argument(
        '--num-epochs',
        dest='epochs',
        metavar='EPOCHS',
        type=int,
        default=15,
        help='Number of epochs to train for')  # yapf: disable
    parser.add_argument(
        '--batch-size',
        dest='batch_size',
        metavar='BATCH-SIZE',
        type=int,
        default=16,
        help='Size of a mini batch')  # yapf: disable
    parser.add_argument(
        '--log',
        dest='log',
        metavar='LOG-FILE',
        type=str,
        default='logs/stats',
        help='Path to output log file')  # yapf: disable
    parser.add_argument(
        '--model',
        dest='model',
        metavar='MODEL-TYPE',
        type=str,
        default='dcnn',
        choices=model_choices,
        help=f'Model to use. One of {model_choices}')  # yapf: disable
    parser.add_argument(
        '--lr',
        dest='learning_rate',
        metavar='LEARNING-RATE',
        type=float,
        default=0.05,
        help='Learning rate')  # yapf: disable
    parser.add_argument(
        '--embed-dim',
        dest='embedding_dim',
        metavar='EMBED-DIMENSION',
        type=int,
        default=60,
        help='Dimension of the word embeddings')  # yapf: disable
    parser.add_argument(
        '--eval-period',
        dest='eval_period',
        metavar='NUM-BATCHES',
        type=int,
        default=200,
        help='Number of training batches between validation evals')  # yapf: disable

    return parser.parse_args()

def get_model(model_name):
    if model_name == 'dcnn':
        # create a dynamic cnn model
        model = models.DCNN(num_embeddings, embedding_dim, num_classes)
        print('Running model DCNN')
    elif model_name == 'dcnn-relu':
        # create a dynamic cnn model with ReLU activations
        model = models.DCNNReLU(num_embeddings, embedding_dim, num_classes)
        print('Running model DCNNReLU')
    elif model_name == 'dcnn-leakyrelu':
        # create a dynamic cnn model with ReLU activations
        model = models.DCNNLeakyReLU(num_embeddings, embedding_dim, num_classes)
        print('Running model DCNNLeakyReLU')
    elif model_name == 'mlp':
        # create an mlp model to compare against
        max_length = max(len(x.text) for x in train_iter.data())
        model = models.MLP(num_embeddings, embedding_dim, max_length, num_classes)
        print('Running model MLP')
    if torch.cuda.is_available():
        model = model.cuda()
    return model

def calc_accuracy(outputs, targets):
    correct = (outputs.data.max(dim=1)[1] == targets.data)
    return torch.sum(correct) / targets.size()[0]


if __name__ == '__main__':
    args = get_arguments()
    num_epochs = args.epochs
    batch_size = args.batch_size
    lr = args.learning_rate
    embedding_dim = args.embedding_dim

    device = None if torch.cuda.is_available() else -1  # None == GPU, -1 == CPU
    load_data = dataloader.twitter(embedding_dim=embedding_dim, batch_size=batch_size, device=device)

    train_iter, val_iter, test_iter = load_data()
    val_iter.sort_key = test_iter.sort_key = lambda example: len(example.text)
    num_embeddings = len(train_iter.dataset.fields['text'].vocab)
    num_classes = len(train_iter.dataset.fields['label'].vocab)

    model = get_model(args.model)

    criterion = torch.nn.CrossEntropyLoss()
    optimizer = torch.optim.Adagrad(model.params(), lr=lr)

    log = logger.Logger(args.log)

    # `stats` has form [train_loss, train_acc, test_loss, test_acc]
    stats = np.zeros(4, dtype='float64')
    eval_period = args.eval_period
    with tqdm.tqdm(train_iter, total=len(train_iter) * num_epochs) as progress:
        for i, batch in enumerate(train_iter):
            optimizer.zero_grad()

            outputs = model(batch.text)
            loss = criterion(outputs, batch.label)
            loss.backward()
            optimizer.step()

            stats[0] += loss.data[0]
            stats[1] += calc_accuracy(outputs, batch.label)

            progress.update()
            if (i % eval_period) == (eval_period - 1):
                for batch in val_iter:
                    outputs = model(batch.text)
                    loss = criterion(outputs, batch.label)
                    stats[2] += loss.data[0]
                    stats[3] += calc_accuracy(outputs, batch.label)
                stats[:2] /= eval_period
                stats[2:] /= len(val_iter)
                log.log(stats.astype('float32'))
                progress.set_postfix(val_loss=stats[2], train_loss=stats[0])
                stats[:] = 0
            if train_iter.epoch >= num_epochs:
                break
