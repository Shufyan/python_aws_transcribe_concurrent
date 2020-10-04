"""
Purpose

Contains all the necessary parameters to be controlled externally to make the functionality more generic.

    config = {
        'aws_auth_cred':
            {
                'aws_access_key_id': '<Your aws access key id>',
                'aws_secret_access_key': '<Your aws seceret key>',
                'region':'<Your aws region>'
            },   
        'aws_s3_config': {
            'bucket_name': '<Add input bucket name>',
            'out_bucket_name': '<Add output bucket name>'
        },
        'aws_transcribe_config': {
            'job_prefix': '<Add a job prefix>',             # You must add a Job Prefix to list all jobs with specific prefix
            'vocabulary_name': '<Add a vocublary name>',
            'phrases': ['<Add a list of phrases>'],
            'media_format': '<Add a media fomat mp3|mp4|wav etc.>',         # Keep blank '' if you want aws to detect automatically.
            'Settings': {
                'ShowSpeakerLabels': '<True|False>',              # True | False
                'MaxSpeakerLabels': '<Add a number>',             # Value must be between (1-10). Note: If you specify the 'max_speaker_labels' field, you must set the 'show_speaker_labels' field to True.
                'ShowAlternatives': '<True|False>',               # True | False
                'MaxAlternatives': '<Add a number>',              # Value must be between (1-10). Note: If you specify the 'max_alternatives' field, you must set the 'show_alternatives' field to True.
            },
            'JobExecutionSettings': {
                'AllowDeferredExecution': '<True|False>',         # True | False 
                'DataAccessRoleArn': '<Add the role ARN>',        # If you specify the 'allow_deferred_execution' field, you must specify the 'data_access_rolearn' field.    
            }
        },
        'file_paths': {
            'input_path': '<Add the input folder path>',
            'output_path': '<Add the output folder path>',
            'archive_path': '<Add the archive path>'
        }
    }
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
		'bucket_name': '<Add input bucket name>',
		'out_bucket_name': '<Add output bucket name>'
	},
	'aws_transcribe_config': {
		'job_prefix': '<Add a job prefix>',             # You must add a Job Prefix to list all jobs with specific prefix
		'vocabulary_name': '<Add a vocublary name>',
		'phrases': ['<Add a list of phrases>'],
		'media_format': '<Add a media fomat mp3|mp4|wav etc.>',         # Keep blank '' if you want aws to detect automatically.
		'Settings': {
			'ShowSpeakerLabels': '<True|False>',              # True | False
			'MaxSpeakerLabels': '<Add a number>',             # Value must be between (1-10). Note: If you specify the 'max_speaker_labels' field, you must set the 'show_speaker_labels' field to True.
			'ShowAlternatives': '<True|False>',               # True | False
			'MaxAlternatives': '<Add a number>',              # Value must be between (1-10). Note: If you specify the 'max_alternatives' field, you must set the 'show_alternatives' field to True.
		},
		'JobExecutionSettings': {
			'AllowDeferredExecution': '<True|False>',         # True | False 
			'DataAccessRoleArn': '<Add the role ARN>',        # If you specify the 'allow_deferred_execution' field, you must specify the 'data_access_rolearn' field.    
		}
	},
	'file_paths': {
		'input_path': '<Add the input folder path>',
		'output_path': '<Add the output folder path>',
		'archive_path': '<Add the archive path>'
	}
}