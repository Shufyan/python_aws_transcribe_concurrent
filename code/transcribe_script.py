"""
Purpose

Shows how to use the AWS SDK for Python (Boto3) with the Amazon Transcribe API to
transcribe an audio file to a text file. Also to export the transription JSON results
into a meaningful Word docx file using Tscribe module.

More about Tscribe can be found here: https://pypi.org/project/tscribe/

Note: In this example, the transcription jobs are processed concurrently. Hence, Job Queuing is implemented. 

This example uses a main() function to execute all the following steps in order:

    1. Rename all the input files into an acceptable name format, input path picked up from configuration.
    2. Create buckets if not available and uploads all the input files into input bucket, 
       input & output bucket name picked up from configuration.
    3. Transcribes all the input audio files concurrently to save a lot of time.
    4. All COMPLETED and FAILED jobs are separated and job results are exported into their respective csv file(s). 
       The files  for e.g. 'job_summary_completed_xxxxxx.csv' are placed in output folder. 
    5. Finally, the resulted JSON files are converted into a more meaningful Word docx file using Tscribe module 
       and both JSON & Docx are exported into the output folder. The successfully completed audio files & resulted 
       JSON are archived into 'Archive' folder. Jobs are deleted as a cleanup process on completion of the whole activity.
"""

# Importing the all required modules.
import logging
import sys
import time
import datetime
import os
import boto3
from botocore.exceptions import ClientError
import requests
import transcribe_basics as tb
from parameters import config
import tscribe
import csv
import json
import re

sys.path.append('')
from custom_waiter import CustomWaiter, WaitState

logger = logging.getLogger(__name__)

class TranscribeAndExport():
    """
    This class contains all the requied methods and functionalities for the execution. 
    """
    def __init__(self):
        self.s3_resource = boto3.resource('s3', 
                                    aws_access_key_id = config['aws_auth_cred']['aws_access_key_id'], 
                                    aws_secret_access_key = config['aws_auth_cred']['aws_secret_access_key'],
                                    region_name = config['aws_auth_cred']['region'])

        self.transcribe_client = boto3.client('transcribe', 
                                    aws_access_key_id = config['aws_auth_cred']['aws_access_key_id'], 
                                    aws_secret_access_key = config['aws_auth_cred']['aws_secret_access_key'],
                                    region_name = config['aws_auth_cred']['region'])

        self.bucket_name = config['aws_s3_config']['bucket_name']
        self.output_bucket_name = config['aws_s3_config']['out_bucket_name']
        self.input_path = config['file_paths']['input_path']
        self.output_path = config['file_paths']['output_path']


    def rename_files(self, folder_path):
        """
        Renames all the special character's into '-' for each file in a folder. 
        """
        try:
            for file in os.listdir(folder_path):
                file_name, file_extn = os.path.splitext(file)
                src = folder_path + file
                converted_file_name = re.sub('[^a-zA-Z0-9\n\.]', '-', file_name)
                dst = folder_path + converted_file_name + file_extn
                os.rename(src,dst)
        except Exception:
            logger.exception('Something went wrong in "rename_files"')


    def upload_files(self):
        """
        Create input & output bucket(s) if already not available and upload the audio files into input bucket. 
        """
        try:
            """ Shows how to use the Amazon Transcribe service. """
            logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')        

            bucket = self.s3_resource.Bucket(self.bucket_name)
            
            print(f"Creating bucket {self.bucket_name}.")
            if self.transcribe_client.meta.region_name == 'us-east-1':
                bucket = self.s3_resource.create_bucket(
                Bucket=self.bucket_name)
                self.s3_resource.create_bucket(
                Bucket=self.output_bucket_name)
            else:    
                bucket = self.s3_resource.create_bucket(
                    Bucket=self.bucket_name,
                    CreateBucketConfiguration={
                        'LocationConstraint': self.transcribe_client.meta.region_name})
                self.s3_resource.create_bucket(
                    Bucket=self.output_bucket_name,
                    CreateBucketConfiguration={
                        'LocationConstraint': self.transcribe_client.meta.region_name})

            files = [f for f in os.listdir(self.input_path)]

            for file in files:
                media_file_name = self.input_path + file
                media_object_key = file
                print(f"Uploading media file {media_file_name}.")
                bucket.upload_file(media_file_name, media_object_key)

        except ClientError:
            logger.exception("Failed to upload files.")
            raise


    def transcribe_files(self):
        """
        Transcribe all the audio files from the input bucket concurrently and save the 
        resulted JSON into the output bucket. A custom vocabulary is also created to
        improve the transcrition result.
        """
        try:
            """ Shows how to use the Amazon Transcribe service. """
            logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

            bucket = self.s3_resource.Bucket(self.bucket_name) 

            for file in bucket.objects.filter(Delimiter='/'):
                try:
                    print('-'*88)
                    print("Creating a custom vocabulary that lists the nonsense words to try to "
                        "improve the transcription.")
                    if config['aws_transcribe_config']['vocabulary_name'] is not None:
                        vocabulary_name = config['aws_transcribe_config']['job_prefix'] + '-' + config['aws_transcribe_config']['vocabulary_name']

                        try:
                            self.transcribe_client.get_vocabulary(VocabularyName=vocabulary_name)
                        except ClientError:
                            logger.info("Couldn't find vocabulary %s. Therefore, creating a new one.", vocabulary_name)                
                            tb.create_vocabulary(
                                vocabulary_name, 'en-US', self.transcribe_client,
                                phrases = config['aws_transcribe_config']['phrases'],
                                )
                            vocabulary_ready_waiter = tb.VocabularyReadyWaiter(self.transcribe_client)
                            vocabulary_ready_waiter.wait(vocabulary_name)
                    else:
                        vocabulary_name = None

                    job_name = config['aws_transcribe_config']['job_prefix'] + '-' + f'{file.key}'
                    print(f"Starting transcription job {job_name}.")
                    media_format = config['aws_transcribe_config']['media_format']
                    tb.start_job(
                        job_name, f's3://{self.bucket_name}/{file.key}', media_format, 'en-US',
                        self.transcribe_client, vocabulary_name)
                except:
                    logger.info(f'Something went wrong with job: {job_name}', exc_info=True)
                    continue
        except ClientError:
            logger.exception("Failed to transcribe jobs.")
            raise


    def export_files(self):
        """
        Export all the resulted JSON file(s) as Word docx using Tscribe and archive the source files in 'Archive' folder. 
        """
        try:
            logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

            bucket = self.s3_resource.Bucket(self.output_bucket_name)
            archive_path = config['file_paths']['archive_path']

            for obj in bucket.objects.filter(Delimiter='/'):
                obj_name, obj_extn = os.path.splitext(obj.key)
                if obj_extn == '.json':
                    self.s3_resource.meta.client.download_file(self.output_bucket_name, obj.key, os.path.join(self.output_path, obj.key))
                    file_content = obj.get()['Body'].read().decode('utf-8')
                    json_content = json.loads(file_content)
                    if json_content['results']['transcripts'][0]['transcript'] != "" :
                        json_file_path = os.path.join(self.output_path, obj.key)
                        save_as_path = os.path.join(self.output_path, obj_name +'.docx')
                        tscribe.write(json_file_path, format="docx", save_as= save_as_path)
                        self.archive_object(archive_path, '', '', obj.key)
                        
        except ClientError:
            logger.exception("Failed to export files.")
            raise


    def archive_object(self, archive_path = '', input_obj_path = '', output_obj_path = '', object_name = ''):
        """
        Archive the source audio & resulted JSON object into the provided archive path. 
        """
        obj_name, obj_extn = os.path.splitext(object_name)
        if obj_extn == '.json':
            try:
                input_obj_name = obj_name.lstrip(config['aws_transcribe_config']['job_prefix'] + '-')
                self.s3_resource.Object(self.bucket_name, archive_path +'/'+ input_obj_name).copy_from(CopySource=self.bucket_name +'/' + input_obj_path + input_obj_name)
                self.s3_resource.Object(self.bucket_name, input_obj_path + input_obj_name).delete()
            except ClientError as e:
                if(e.response['Error']['Code']) == 'NoSuchKey':                
                    print(f'Object {input_obj_path + input_obj_name} not found.')                        

            try:
                self.s3_resource.Object(self.output_bucket_name, archive_path +'/'+ object_name).copy_from(CopySource=self.output_bucket_name +'/' + output_obj_path + object_name)
                self.s3_resource.Object(self.output_bucket_name, output_obj_path + object_name).delete()
            except ClientError as e:
                if(e.response['Error']['Code']) == 'NoSuchKey':                
                    print(f'Object {output_obj_path + object_name} not found.')


    def validate_field(self, field):
        """
        Validate existence of field and set with a blank ('') value if field does not exist. 
        """
        try:
            if field:
                pass
            else:
                field = ''
            return field
        except Exception:
            logger.exception('Something went wrong with "validate_field" method.')


    def job_summary(self, job_list, job_status):
        """
        Creates a job summary report for all COMPLETED and FAILED jobs. 
        """
        ns = f'{time.time_ns()}'
        try:
            if job_status == "COMPLETED":
                writer = csv.writer(open(os.path.join(self.output_path,'job_summary_completed_'+ ns +'.csv'), 'w', newline=''))
                writer.writerow(['TranscriptionJobName',
                                'CreationTime',	
                                'StartTime',	
                                'CompletionTime',	
                                'LanguageCode',	
                                'TranscriptionJobStatus',	
                                'OutputLocationType'
                                ])

                for job in job_list:
                    writer.writerow([self.validate_field(job['TranscriptionJobName']),
                                self.validate_field(f"{job['CreationTime']}"),	
                                self.validate_field(f"{job['StartTime']}"),	
                                self.validate_field(f"{job['CompletionTime']}"),	
                                self.validate_field(job['LanguageCode']),	
                                self.validate_field(job['TranscriptionJobStatus']),	
                                self.validate_field(job['OutputLocationType'])
                                ])

            elif job_status == "FAILED":
                    writer = csv.writer(open(os.path.join(self.output_path,'job_summary_failed_'+ ns +'.csv'), 'w', newline=''))
                    writer.writerow(['TranscriptionJobName',
                                    'CreationTime',	
                                    'StartTime',	
                                    'LanguageCode',	
                                    'TranscriptionJobStatus',
                                    'FailureReason',	
                                    'OutputLocationType'
                                    ])

                    for job in job_list:
                        writer.writerow([self.validate_field(job['TranscriptionJobName']),
                                    self.validate_field(f"{job['CreationTime']}"),	
                                    self.validate_field(f"{job['StartTime']}"),	
                                    self.validate_field(job['LanguageCode']),	
                                    self.validate_field(job['TranscriptionJobStatus']),                                    	
                                    self.validate_field(job['FailureReason']),	
                                    self.validate_field(job['OutputLocationType'])
                                    ])

        except Exception:
            logger.exception("Error occured in 'job_summary' method.")


    def archive_processed_files(self, archive_path = '', input_obj_path = '', output_obj_path = ''):
        """
        Archive all the files by object name inside the input & output folder. 
        """
        output_bucket = self.s3_resource.Bucket(self.output_bucket_name)

        for obj in output_bucket.objects.filter(Delimiter='/'):
            obj_name, obj_extn = os.path.splitext(obj.key)
            if obj_extn == '.json':
                try:
                    input_obj_name = obj_name.lstrip(config['aws_transcribe_config']['job_prefix'] + '-')
                    self.s3_resource.Object(self.bucket_name, archive_path +'/'+ input_obj_name).copy_from(CopySource=self.bucket_name +'/' + input_obj_path + input_obj_name)
                    self.s3_resource.Object(self.bucket_name, input_obj_path + input_obj_name).delete()
                except ClientError as e:
                    if(e.response['Error']['Code']) == 'NoSuchKey':                
                        print(f'Object {input_obj_path + input_obj_name} not found.')                        

                try:
                    self.s3_resource.Object(self.output_bucket_name, archive_path +'/'+ obj.key).copy_from(CopySource=self.output_bucket_name +'/' + output_obj_path + obj.key)
                    self.s3_resource.Object(self.output_bucket_name, output_obj_path + obj.key).delete()
                except ClientError as e:
                    if(e.response['Error']['Code']) == 'NoSuchKey':                
                        print(f'Object {output_obj_path + obj.key} not found.')


def main():
    """
    This method executes all the steps in order to upload, transcribe and export the results. 
    """
    try:
        ts = TranscribeAndExport()
        print('-'*88)
        print("Welcome to the Amazon Transcribe!")
        print('-'*88)

        # Printing the start time
        t = time.localtime()
        start_time = time.strftime("%H:%M:%S", t)
        print(f'Start time: {start_time}')

        # Renaming files in acceptable format
        ts.rename_files(config['file_paths']['input_path'])

        # Uploading audio files into input bucket
        ts.upload_files()

        # Running transcription on source input files
        ts.transcribe_files()


        all_jobs = tb.list_jobs(config['aws_transcribe_config']['job_prefix'], ts.transcribe_client)
        for job in all_jobs:
            try:
                print(f"job['TranscriptionJobName']: {job['TranscriptionJobName']}")
                transcribe_waiter = tb.TranscribeCompleteWaiter(ts.transcribe_client)
                transcribe_waiter.max_tries = 120
                transcribe_waiter.wait(job['TranscriptionJobName'])
            except:
                logger.info(f'Something went wrong with job in all_jobs: {job["TranscriptionJobName"]}', exc_info=True)
                continue
        
        # Need to instantiate the 'transcribe' client again to fetch latest job updates
        trans_client = boto3.client('transcribe', 
                                        aws_access_key_id = config['aws_auth_cred']['aws_access_key_id'], 
                                        aws_secret_access_key = config['aws_auth_cred']['aws_secret_access_key'],
                                        region_name = config['aws_auth_cred']['region'])                                        

        all_processed_jobs = tb.list_jobs(config['aws_transcribe_config']['job_prefix'], trans_client)
        print(f'all_jobs after: {all_processed_jobs}')
        all_completed_jobs = []
        all_failed_jobs = []

        # Separating the COMPLETED & FAILED jobs, generating summary reports and deleting the processed jobs
        for each_job in all_processed_jobs:  
            try:          
                if each_job['TranscriptionJobStatus'] == 'COMPLETED':
                    all_completed_jobs.append(each_job)
                elif each_job['TranscriptionJobStatus'] == 'FAILED':
                    all_failed_jobs.append(each_job)
            except ClientError:
                logger.exception(f'Something went wrong with job in all_processed_jobs: {job["TranscriptionJobName"]}')
                pass
        
        # COMPLETED Jobs
        if len(all_completed_jobs) > 0:
            print(f'all_completed_jobs: {all_completed_jobs}')
            ts.job_summary(all_completed_jobs, 'COMPLETED')

            for job in all_completed_jobs:
                tb.delete_job(job['TranscriptionJobName'], trans_client)

        # FAILED Jobs
        if len(all_failed_jobs) > 0:
            print(f'all_failed_jobs: {all_failed_jobs}')
            ts.job_summary(all_failed_jobs, 'FAILED')

            for job in all_failed_jobs:
                tb.delete_job(job['TranscriptionJobName'], trans_client)        

        # Exporing the resulted JSON file to Word docx and archiving files
        ts.export_files()

        # Printing the end time
        t = time.localtime()
        end_time = time.strftime("%H:%M:%S", t)
        print(f'End time: {end_time}')

    except Exception:
        logger.exception('Fatal error in main loop')

if __name__ == '__main__':
    # Calling the main() function to start execution.
    main()
