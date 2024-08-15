from huggingface_hub import hf_hub_download
from llama_cpp import Llama


model_name = "second-state/E5-Mistral-7B-Instruct-Embedding-GGUF"
model_file = "e5-mistral-7b-instruct-Q3_K_L.gguf"
model_path = hf_hub_download(model_name, filename=model_file)


llm = Llama(
    model_path=model_path,
    n_ctx=16000,
    n_threads=32,
    n_gpu_layers=0,
    embedding=True
)

prompt = "The meaning of life is "
res = llm.embed(prompt)

print(res)
