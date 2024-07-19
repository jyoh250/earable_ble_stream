import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model

class Sleep_Stage_Model():
    '''
    PC Sleep Staging Model Class.
    '''
    def __init__(self, model_fpath, feature_means_fpath, feature_stds_fpath):
        self.feature_means = np.load(feature_means_fpath)
        self.feature_stds = np.load(feature_stds_fpath)
        self.model = self.build_model(model_fpath)
    
    def build_model(self, model_fpath,):
        '''
        Builds Sleep Classification Model from trained model file.
        '''
        model = load_model(model_fpath)
        return model
    
    def predict(self, spectrogram, concat_feature_vector):
        '''
        Predict the probability of the epoch being Sleep given the epoch's spectrogram 
        and EEG/EOG/EMG feature vector.
        '''
        # Scale aggregate feature vector according to the training data distribution
        concat_feature_vector = (concat_feature_vector - self.feature_means)/self.feature_stds
        
        sleep_stage_probs = self.model.predict([np.expand_dims(spectrogram, 0), np.expand_dims(concat_feature_vector, 0)]).squeeze()
        return sleep_stage_probs


class Sleep_Stage_Model_TFLite():
    '''
    TF-Lite Sleep Staging Model Class.
    '''
    def __init__(self, model_fpath, feature_means_fpath, feature_stds_fpath):
        self.feature_means = np.load(feature_means_fpath)
        self.feature_stds = np.load(feature_stds_fpath)
        self.model_interpreter = tf.lite.Interpreter(model_path=model_fpath)
    
    def predict(self, spectrogram, concat_feature_vector):
        '''
        Predict the probability of the epoch being Sleep given the epochs spectrogram 
        and EEG/EOG/EMG feature vector using TF-Lite Model.
        '''
        spectrogram_input = spectrogram.squeeze()
        spectrogram_input = spectrogram_input.astype(np.float32)
        
        # Scale aggregate feature vector according to the training data distribution
        concat_feature_vector = (concat_feature_vector - self.feature_means)/self.feature_stds
        features_input = concat_feature_vector.squeeze()
        features_input = features_input.astype(np.float32)

        # Initialize the TFLite interpreter
        self.model_interpreter.allocate_tensors()

        input_details_spec = self.model_interpreter.get_input_details()[0]
        input_details_feat = self.model_interpreter.get_input_details()[1]
        output_details = self.model_interpreter.get_output_details()[0]

        self.model_interpreter.set_tensor(input_details_spec['index'], [spectrogram_input])
        self.model_interpreter.set_tensor(input_details_feat['index'], [features_input])
        self.model_interpreter.invoke()
        sleep_stage_probs = self.model_interpreter.get_tensor(output_details['index']).squeeze()
        return sleep_stage_probs