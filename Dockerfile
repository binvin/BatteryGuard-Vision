FROM public.ecr.aws/lambda/python:3.12
COPY requirements-lambda.txt ./
RUN pip install --no-cache-dir -r requirements-lambda.txt
COPY analyzer.py lambda_function.py ${LAMBDA_TASK_ROOT}/
CMD ["lambda_function.lambda_handler"]
