COPY (
  SELECT Resume_str
  FROM 'https://huggingface.co/api/datasets/opensporks/resumes/parquet/default/train/0.parquet'
  LIMIT 50
) TO 'resumes.csv' (HEADER, DELIMITER ',');