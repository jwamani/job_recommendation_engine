from .models import Interaction


def get_latest_save_dismiss_states(user):
    states = {}
    rows = Interaction.objects.filter(
        user=user, action__in=["save", "dismiss"]
    ).values_list("job_id", "action")
    for job_id, action in rows:
        if job_id not in states:
            states[job_id] = action
    return states
