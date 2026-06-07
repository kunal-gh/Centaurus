"""
Centaurus DPO (Direct Preference Optimization) Pipeline.

This script fetches human-reviewed answers from the `reviewer_decisions` table 
and formats them into preference pairs (chosen vs. rejected) for DPO training.
It uses the `trl` library from Hugging Face for lightweight fine-tuning.
"""

import os
import sys
import pandas as pd
from datasets import Dataset
from dotenv import load_dotenv

# Load env variables from root directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

from backend.database import get_supabase

# These imports are optional unless actually running the training loop
try:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from trl import DPOTrainer, DPOConfig
    from peft import LoraConfig
    TRL_AVAILABLE = True
except ImportError:
    TRL_AVAILABLE = False


def fetch_preference_data() -> pd.DataFrame:
    """
    Fetches the resolved escalations from Supabase and formats them into
    (prompt, chosen, rejected) tuples required for DPO.
    """
    print("Fetching reviewer decisions from Supabase...")
    supabase = get_supabase()
    
    # We join with query_logs to get the original prompt (raw_query)
    response = supabase.table("reviewer_decisions") \
        .select("original_response, approved_response, query_logs(raw_query)") \
        .execute()
        
    data = response.data
    if not data:
        print("No reviewer decisions found. Nothing to train on.")
        return pd.DataFrame()
        
    formatted_data = []
    for row in data:
        prompt = row.get("query_logs", {}).get("raw_query", "")
        rejected = row.get("original_response", "")
        chosen = row.get("approved_response", "")
        
        if prompt and rejected and chosen:
            formatted_data.append({
                "prompt": prompt,
                "chosen": chosen,
                "rejected": rejected
            })
            
    df = pd.DataFrame(formatted_data)
    print(f"Generated {len(df)} preference pairs.")
    return df


def train_dpo_model(df: pd.DataFrame, model_name: str = "gpt2"):
    """
    Example DPO training loop using LoRA.
    Replace `model_name` with the actual base model (e.g., Llama-3-8B).
    """
    if not TRL_AVAILABLE:
        print("Please install torch, transformers, peft, and trl to run DPO training.")
        print("pip install torch transformers peft trl")
        return

    print(f"Initializing DPOTrainer for model: {model_name}")
    
    # Convert pandas dataframe to Hugging Face Dataset
    dataset = Dataset.from_pandas(df)
    
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Load model in 8-bit or standard depending on hardware.
    # For demonstration, we load normally.
    model = AutoModelForCausalLM.from_pretrained(model_name, device_map="auto")
    
    # We need a reference model for DPO (usually the same base model, frozen)
    ref_model = AutoModelForCausalLM.from_pretrained(model_name, device_map="auto")
    
    # Configure LoRA to make training lightweight
    peft_config = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )
    
    training_args = DPOConfig(
        output_dir="./dpo_results",
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        learning_rate=5e-5,
        num_train_epochs=3,
        logging_steps=10,
        remove_unused_columns=False,
    )
    
    trainer = DPOTrainer(
        model=model,
        ref_model=ref_model,
        args=training_args,
        train_dataset=dataset,
        tokenizer=tokenizer,
        peft_config=peft_config,
    )
    
    print("Starting DPO training...")
    trainer.train()
    
    output_path = "./centaurus-dpo-lora"
    trainer.save_model(output_path)
    print(f"Model saved to {output_path}")


if __name__ == "__main__":
    df = fetch_preference_data()
    if not df.empty:
        # For a real pipeline, use a stronger base model like meta-llama/Meta-Llama-3-8B-Instruct
        # Note: running this locally requires significant GPU VRAM.
        print("Run `train_dpo_model(df)` on a GPU-enabled machine to start training.")
        # train_dpo_model(df, "gpt2")
