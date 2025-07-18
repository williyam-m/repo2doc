'''
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch
from admin_console.ai_model_config import *

generator = None

def load_qwen_model_from_transformer():
    global generator
    if ModelConfig.isQwenFromTransformerEnabled() and generator is None:
        tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen1.5-7B-Chat")
        model = AutoModelForCausalLM.from_pretrained(
            "Qwen/Qwen1.5-7B-Chat",
            device_map="auto",
            torch_dtype=torch.float16
        )
        generator = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
        )
    return generator
'''