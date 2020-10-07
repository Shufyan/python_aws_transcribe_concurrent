"""
Purpose

Contains all the necessary parameters to be controlled externally to make the functionality more generic.
"""

import time
import datetime

curr_time = datetime.datetime.now()

config = {
	'aws_auth_cred':
		{
			'aws_access_key_id': '<Your aws access key id>',
			'aws_secret_access_key': '<Your aws seceret key>',
			'region':'<Your aws region>'
		},   
	'aws_s3_config': {
		'bucket_name': 'input.mytestbucket.com',
		'out_bucket_name': 'output.mytestbucket.com'
	},
	'aws_transcribe_config': {
		'job_prefix': 'shufyan',             # You must add a Job Prefix to list all jobs with specific prefix
		'vocabulary_name': 'test1-vocab',
		'phrases': ['brillig', 'slithy', 'borogoves', 'mome', 'raths', 'Jub-Jub', 'frumious',
            'manxome', 'Tumtum', 'uffish', 'whiffling', 'tulgey', 'thou', 'frabjous',
            'callooh', 'callay', 'chortled'],
		'media_format': 'mp4',         # Keep blank '' if you want aws to detect automatically.
		'Settings': {
			'ShowSpeakerLabels': True,         # True | False
			'MaxSpeakerLabels': 6,             # Value must be between (1-10). Note: If you specify the 'max_speaker_labels' field, you must set the 'show_speaker_labels' field to True.
			'ShowAlternatives': True,          # True | False
			'MaxAlternatives': 4,              # Value must be between (1-10). Note: If you specify the 'max_alternatives' field, you must set the 'show_alternatives' field to True.
		},
		'JobExecutionSettings': {
			'AllowDeferredExecution': True,         # True | False 
			'DataAccessRoleArn': 'arn:aws:iam::<aws_account_id>:role/<role_name>',        # If you specify the 'allow_deferred_execution' field, you must specify the 'data_access_rolearn' field.    
		}
	},
	'file_paths': {
		'input_path': '../input/',
		'output_path': '../output/',
		'archive_path': f'archive/{curr_time.year}' + '/' + f'{curr_time.month}' + '/' + f'{curr_time.day}'
	}
}