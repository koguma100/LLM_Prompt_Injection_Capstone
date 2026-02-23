COPY (
  WITH zeros AS (
    SELECT text, label FROM 'https://huggingface.co/api/datasets/jayavibhav/prompt-injection/parquet/default/train/0.parquet'
    WHERE label = 0
    --ORDER BY random()
    LIMIT 500
  ),
  ones AS (
    SELECT text, label FROM 'https://huggingface.co/api/datasets/jayavibhav/prompt-injection/parquet/default/train/0.parquet'
    WHERE label = 1
   -- ORDER BY random()
    LIMIT 500
  )
  SELECT * FROM zeros
  UNION ALL
  SELECT * FROM ones
  --ORDER BY random()
) TO 'hugging-face-samples.csv' (HEADER, DELIMITER ',');
