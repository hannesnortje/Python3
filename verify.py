import onnxruntime as ort
import numpy as np

# Load the ONNX model
session = ort.InferenceSession("resnet50.onnx")

# Create a dummy input
dummy_input = np.random.randn(1, 3, 224, 224).astype(np.float32)

# Run inference
outputs = session.run(None, {"input": dummy_input})

# Print the output
print(outputs)
