import os

def save_to_csv(folder, file_name, df):

  if not os.path.exists(folder):
      os.makedirs(folder)

  file_path = os.path.join(folder, file_name)
  df.to_csv(file_path, index=False, encoding='utf-8')