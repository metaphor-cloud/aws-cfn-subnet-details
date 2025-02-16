FROM public.ecr.aws/lambda/python:3.13
COPY src /app
WORKDIR /app
# RUN pip install -r requirements.txt
CMD ["index.handler"]

