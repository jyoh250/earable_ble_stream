import numpy as np
import tensorflow as tf

class GazeSQCModelTFLite():
    '''
    TF-Lite Gaze SQC model class.
    '''
    def __init__(self, model_fpath, feature_means_fpath, feature_stds_fpath):
        self.feature_means = np.load(feature_means_fpath)
        self.feature_stds = np.load(feature_stds_fpath)
        self.model_interpreter = tf.lite.Interpreter(model_path=model_fpath)
    
    def predict(self, feature_vector):
        '''
        Predict the probability of a signal segment having bad signal quality given
        its input feature vector.
        '''
        # Scale feature vector according to the training data distribution
        feature_vector = (feature_vector - self.feature_means)/self.feature_stds
        features_input = feature_vector.squeeze()
        features_input = features_input.astype(np.float32)

        # Initialize the TFLite interpreter
        self.model_interpreter.allocate_tensors()

        input_details_feat = self.model_interpreter.get_input_details()[0]
        output_details = self.model_interpreter.get_output_details()[0]

        self.model_interpreter.set_tensor(input_details_feat['index'], [features_input])
        self.model_interpreter.invoke()
        bad_signal_probs = self.model_interpreter.get_tensor(output_details['index']).squeeze()
        return bad_signal_probs