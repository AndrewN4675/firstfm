import djangoRoute from "../routes/djangoApi";
import csrfRoute from "../routes/csrfApi";

export type Username = {
    username: string,
}

export async function fetchUserInfo() {
    const {data} = await djangoRoute.get<Username>('itsme/');

    return data;
}

export async function logIntoLastFM() {
    const {data} = await csrfRoute.get('lastfm/start/');
    window.location.assign(data.auth_url);
}
