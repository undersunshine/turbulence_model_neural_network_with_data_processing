import os
import tensorflow as tf
import inference
import numpy as np
import time

BATCH_SIZE = 49152
LEARNING_RATE_BASE = 0.1
LEARNING_RATE_DECAY = 0.9998
REGULARIZATION_RATE = 0.000001
TRAINING_STEPS = 2000000
MOVING_AVERAGE_DECAY = 0.99

MODEL_SAVE_PATH = "./model/"
MODEL_NAME = "model.ckpt"
SUMMARY_DIR = "./log/"

def train(train_data, train_labels):
    x = tf.placeholder(
        tf.float32, [None, inference.INPUT_NODE], name='x-input')
    y_ = tf.placeholder(
        tf.float32, [None, inference.OUTPUT_NODE], name='y-input')
    regularizer = tf.contrib.layers.l2_regularizer(REGULARIZATION_RATE)
    y = inference.inference(x, regularizer)
    global_steps = tf.Variable(0, trainable=False)
    variable_averages = tf.train.ExponentialMovingAverage(
        MOVING_AVERAGE_DECAY, global_steps)
    variables_averages_op = variable_averages.apply(
        tf.trainable_variables())
    error = tf.reduce_mean(tf.square(y - y_)) + tf.add_n(tf.get_collection('errors'))
    # tf.summary.scalar('mse', error)
    # learning_rate = 0.1
    learning_rate = tf.train.exponential_decay(LEARNING_RATE_BASE, global_steps, 100, LEARNING_RATE_DECAY, staircase=True)
    # tf.summary.scalar('learning_rate', learning_rate)
    train_step = tf.train.GradientDescentOptimizer(learning_rate).minimize(error, global_step=global_steps)

    # summary_op = tf.summary.merge_all()
    with tf.control_dependencies([train_step, variables_averages_op]):
        train_op = tf.no_op(name='train')

    saver = tf.train.Saver()
    with tf.Session() as sess:
        # summary_writer = tf.summary.FileWriter(SUMMARY_DIR, sess.graph)
        # tf.global_variables_initializer().run()
        tf.initialize_all_variables().run()
        data_sum= []
        #error_r =[]
        starttime = time.clock()
        for i in range(TRAINING_STEPS):
            start = (i * BATCH_SIZE) % len(train_data)
            end = min(start + BATCH_SIZE, len(train_data))
            xs = train_data[start:end]
            ys = train_labels[start:end]
            [_, error_value, step] = sess.run([train_op, error, global_steps], feed_dict={x: xs, y_: ys})
            if i == 0 or (i + 1) % 1000 == 0:
                [error_value, y_value,learning_rate_value] = sess.run([error, y,learning_rate],
                                                                      feed_dict={x: train_data, y_: train_labels})
                endtime = time.clock()
                print("After %d training steps, error is %g, learning rate is %g, time used is %g"
                      % (step, error_value, learning_rate_value, endtime - starttime))
                # print(y_value)
                data_sum1 = []
                data_sum1.append(i)
                data_sum1.append(error_value)
                tmp = np.mean((train_labels-y_value)**2,axis=0)
                print(tmp)
                data_sum.append(data_sum1)
                if i == 0 :
                    error_r = tmp.reshape(1, -1)
                else:
                    error_r = np.vstack((error_r, tmp.reshape(1,-1)))
                np.savetxt("./self_predict/error_summary.txt", data_sum)
                np.savetxt("./self_predict/error_summary2.txt", error_r)
                np.savetxt("./self_predict/predict_y.txt", y_value)
                saver.save(sess, os.path.join(MODEL_SAVE_PATH, MODEL_NAME), global_step=global_steps)
                # summary_writer.add_summary(summary, i)
    # summary_writer.close()


def main(argv=None):
    inputs = []
    with open('./data_pre_process/clean_data/SAD/input_layer.txt') as f1:
        for line in f1.readlines():
            temp = line.split()
            temp2 = []
            for temp1 in temp:
                temp2.append(float(temp1))
            inputs.append(temp2)
    labels = []
    with open('./data_pre_process/clean_data/SAD/output_layer.txt') as f2:
        for line in f2.readlines():
            temp = line.split()
            temp2 = []
            for temp1 in temp:
                temp2.append(float(temp1))
            labels.append(temp2)

    train_data = inputs
    train_labels = labels
    train(train_data, train_labels)


if __name__ == '__main__':
    tf.app.run()
