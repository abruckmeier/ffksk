from typing import Tuple
from slack_sdk import WebClient
from django.conf import settings
from slack_sdk.errors import SlackApiError


def get_user_information(name: str) -> Tuple[bool, str, str]:
    """"""

    found_id: str = ''
    error: bool = False
    return_msg: str = ''

    slack_token = getattr(settings,'SLACK_O_AUTH_TOKEN')
    sc = WebClient(slack_token)

    # First, check, if name is already the id
    try:
        response = sc.users_info(user=name)
        found_id = name
        return_msg = f'Found name. Was already the id.'

    except SlackApiError as e:
        # We need to find the user id by searching for the name

        # Try to find the given Slack-User in the user list on slack
        users = []
        next_cursor = ''
        next_iteration = True

        while next_iteration:
            ulist = sc.users_list(limit=100, cursor=next_cursor)

            if not ulist.get('ok'):
                # No successful return of the members list
                error = True
                return_msg = 'Response from Slack was not ok.'
                next_iteration = False
            else:
                _users = [
                     {'id':x.get('id'), 'name':x.get('name'), 'real_name':x.get('real_name')}
                     for x in ulist.get('members',[])
                ]
                users.extend(_users)
                next_cursor = ulist.get('response_metadata',{}).get('next_cursor','')

                matched_real_name = [x['id'] for x in _users if x['real_name'] == name or x['name'] == name]
                if matched_real_name:
                    found_id = matched_real_name[0]
                if not found_id:
                    matched_id = [x['id'] for x in _users if x['id'] == name]
                    if matched_id:
                        found_id = matched_id[0]

                if found_id:
                    return_msg = 'Found name.'
                    next_iteration = False

                if not found_id and not next_cursor:
                    error = True
                    return_msg = 'End of users list. Found no name.'
                    next_iteration = False

    return error, found_id, return_msg
