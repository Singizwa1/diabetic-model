import joblib
import pandas as pd

artifact = joblib.load('saved_model/model.pkl')
print('='*60)
print('MODEL TRAINING COMPLETED SUCCESSFULLY')
print('='*60)
print()
print('Selected Model:', artifact['model_name'])
print()
print('Model Metrics:')
metrics = artifact['selected_metrics']
for key, value in metrics.items():
    if isinstance(value, float):
        print(f'  {key}: {value:.4f}')
    else:
        print(f'  {key}: {value}')
print()
print('All Models Comparison:')
df = pd.DataFrame(artifact['metrics'])
print(df.to_string(index=False))
print()
print('Trained at:', artifact.get('trained_at_utc', 'N/A'))
print('Model saved to: saved_model/model.pkl')
