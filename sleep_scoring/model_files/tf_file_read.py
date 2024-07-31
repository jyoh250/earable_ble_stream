# from https://www.tensorflow.org/lite/guide/inference#load_and_run_a_model_in_python
# Load a TFLite model and check input and output details.
# and print the structure of the model
# date: 2024-07

import tensorflow as tf

# Load the TFLite model and allocate tensors.
interpreter = tf.lite.Interpreter(model_path='./auto_sleep_scoring_model_ep_rnn_v2.6.2.tflite')
interpreter.allocate_tensors()

# Get input and output tensors.
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

# Print input details
# print("Input details:")
# for input_detail in input_details:
#     print(input_detail)

# # Print output details
# print("Output details:")
# for output_detail in output_details:
#     print(output_detail)

# Get the model's tensor details.
tensor_details = interpreter.get_tensor_details()

# Print tensor details
print("Tensor details:")
for tensor in tensor_details:
    print(tensor)

# get mode's architecture
# print("Model architecture:")
# print(interpreter._interpreter._model)

# Get model's operations
# print("Operations:")
# for i in range(interpreter._interpreter.OperatorCodesLength()):
#     print(interpreter._interpreter.OperatorCodes(i).BuiltinCode())
print("Operations:")
for i in range(len(tensor_details)):
    tensor = tensor_details[i]
    print(f"Tensor {i}: {tensor['name']}, shape: {tensor['shape']}, dtype: {tensor['dtype']}")
# for op in tensor_details:
#     print(op['builtin_code'])

# Get the model details
# model = interpreter._interpreter._model
# subgraph = model.Subgraphs(0)

# # Iterate through the operators and print the builtin codes
# for op_idx in range(subgraph.OperatorsLength()):
#     op = subgraph.Operators(op_idx)
#     op_code = model.OperatorCodes(op.OpcodeIndex()).BuiltinCode()
#     print(op_code)