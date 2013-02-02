import collections
import github

import hlib.error

Issue = collections.namedtuple('Issue', ['user', 'number', 'title', 'body', 'labels'])

class IssuesError(hlib.error.BaseError):
  def __init__(self, gh_error, **kwargs):
    kwargs['reply_status'] = 503

    if isinstance(gh_error, github.GithubException):
      kwargs['msg'] = '%(status)s - %(data)s'
      kwargs['params'] = {'status': gh_error.status, 'data': gh_error.data['message']}

    else:
      kwargs['msg'] = repr(gh_error)

    super(IssuesError, self).__init__(**kwargs)

class Repository(object):
  def __init__(self, token, repository_name):
    super(Repository, self).__init__()

    self.token = token
    self.repository_name = repository_name

    try:
      self.gh = github.Github(self.token)
      self.user = self.gh.get_user()
      self.repository = self.user.get_repo(self.repository_name)

    except Exception, e:
      raise IssuesError(e)

  def get_issues(self):
    try:
      issues = []

      for issue in self.repository.get_issues():
        issues.append(Issue(None, issue.number, issue.title, issue.body, issue.labels))

    except Exception, e:
      raise IssuesError(e)

    return issues

  def create_new_issue(self, title, body):
    try:
      self.repository.create_issue(title, body = body)

    except Exception, e:
      raise IssuesError(e)
