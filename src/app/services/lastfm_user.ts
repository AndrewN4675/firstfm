import djangoRoute from "../../lib/api/djangoApi";
import csrfRoute from "../../lib/api/csrfApi";

export type Username = {
    username: string,
}

export async function fetchUserInfo() {
    const { data } = await djangoRoute.get<Username>('itsme/');

    return data;
}

export async function logIntoLastFM() {
    const { data } = await csrfRoute.get('lastfm/start/');
    window.location.assign(data.auth_url);
}
