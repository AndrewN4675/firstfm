import djangoRoute from "../routes/djangoApi";

export type Username = {
    username: string,
}

export async function fetchUserInfo() {
    const {data} = await djangoRoute.get<Username>('itsme/');

    return data;
}