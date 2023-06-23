"""Hello Analytics Reporting API V4."""

from apiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials
import argparse
import pandas as pd
from pandas import json_normalize

parser = argparse.ArgumentParser(
    description="""
        Gets the google analytics view
        Usage:
            python ga-view.py --credfile 'service_cred.json' --view '63948351' 
    """
)

parser.add_argument(
    "-c",
    "--credfile",
    required=False,
    help="The credentials json file path, ex: 'service_cred.json",
)

parser.add_argument(
    "-v",
    "--view",
    required=False,
    help="The view id, ex: '63948351'",
)

args = parser.parse_args()
KEY_FILE_LOCATION = args.credfile
VIEW_ID = args.view
SCOPES = ['https://www.googleapis.com/auth/analytics.readonly']


def initialize_analyticsreporting():
  """Initializes an Analytics Reporting API V4 service object.

  Returns:
    An authorized Analytics Reporting API V4 service object.
  """
  credentials = ServiceAccountCredentials.from_json_keyfile_name(
      KEY_FILE_LOCATION, SCOPES)

  # Build the service object.
  analytics = build('analyticsreporting', 'v4', credentials=credentials)

  return analytics


def get_report(analytics):
  """Queries the Analytics Reporting API V4.

  Args:
    analytics: An authorized Analytics Reporting API V4 service object.
  Returns:
    The Analytics Reporting API V4 response.
  """
  return analytics.reports().batchGet(
      body={
        'reportRequests': [
        {
          'viewId': VIEW_ID,
          'dateRanges': [{'startDate': '7daysAgo', 'endDate': 'today'}],
          'metrics': [{'expression': 'ga:sessions'}],
          'dimensions': [{'name': 'ga:country'}]
        }]
      }
  ).execute()


def parse_data(response):
  """Parses the reponse.

  Args:
      response (dict): Reponse object

  Returns:
      dataframe: Pandas data frame.
  """

  reports = response['reports'][0]
  columnHeader = reports['columnHeader']['dimensions']
  metricHeader = reports['columnHeader']['metricHeader']['metricHeaderEntries']

  columns = columnHeader
  for metric in metricHeader:
    columns.append(metric['name'])

  data = json_normalize(reports['data']['rows'])
  data_dimensions = pd.DataFrame(data['dimensions'].tolist())
  data_metrics = pd.DataFrame(data['metrics'].tolist())
  data_metrics = data_metrics.applymap(lambda x: x['values'])
  data_metrics = pd.DataFrame(data_metrics[0].tolist())
  result = pd.concat([data_dimensions, data_metrics], axis=1, ignore_index=True)

  return result


def main():
  analytics = initialize_analyticsreporting()
  response = get_report(analytics)
  result = parse_data(response)
  print(result)
  result.to_csv('report.csv')

if __name__ == '__main__':
  main()
