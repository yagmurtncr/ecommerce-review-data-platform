from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    Trainer,
    TrainingArguments
)
from datasets import Dataset
from sklearn.metrics import accuracy_score
import torch
import logging
from db_config import get_mongo_db
import pandas as pd

logging.basicConfig(level=logging.INFO)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = logits.argmax(axis=1)
    return {"accuracy": accuracy_score(labels, preds)}

def get_mongo_df(collection_name):
    db = get_mongo_db()
    collection = db[collection_name]
    df = pd.DataFrame(list(collection.find({}, {'_id': 0})))
    return df

def train_model(model_name, save_path, train_df, test_df, num_labels):
    print(f"\n>>> {model_name} için eğitim başlıyor...\n")

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=num_labels).to(device)

    train_enc = tokenizer(train_df['text'].tolist(), truncation=True, padding=True, max_length=512)
    test_enc = tokenizer(test_df['text'].tolist(), truncation=True, padding=True, max_length=512)

    train_dataset = Dataset.from_dict({**train_enc, 'label': train_df['label'].tolist()})
    test_dataset = Dataset.from_dict({**test_enc, 'label': test_df['label'].tolist()})

    args = TrainingArguments(
        output_dir=save_path,
        eval_strategy="epoch",
        save_strategy="epoch",
        per_device_train_batch_size=8,
        per_device_eval_batch_size=8,
        num_train_epochs=2,
        weight_decay=0.01,
        load_best_model_at_end=True,
        metric_for_best_model="accuracy",
        logging_dir=f"{save_path}/logs",
        logging_steps=100,
        dataloader_num_workers=8,
        fp16=False
    )

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=train_dataset,
        eval_dataset=test_dataset,
        compute_metrics=compute_metrics
    )

    trainer.train()
    model.save_pretrained(save_path)
    tokenizer.save_pretrained(save_path)

    print(f">>> {model_name} eğitimi tamamlandı. Model {save_path} klasörüne kaydedildi.\n")

if __name__ == '__main__':
    print(">>> Veriler MongoDB'den yükleniyor ve hazırlanıyor...")
    train_df = get_mongo_df("train_reviews").sample(n=10000, random_state=42)
    test_df = get_mongo_df("test_reviews").sample(n=2000, random_state=42)

    train_df['label'] = train_df['label'] - 1
    test_df['label'] = test_df['label'] - 1

    num_labels = 5

    train_model(
        model_name="distilbert-base-uncased",
        save_path="./sentiment_model_distilbert",
        train_df=train_df,
        test_df=test_df,
        num_labels=num_labels
    )
