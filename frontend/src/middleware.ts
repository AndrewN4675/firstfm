import { NextRequest, NextResponse } from 'next/server'

const protectedRoutes = ['/music-map']

export default async function middleware(req: NextRequest) {
  const path = req.nextUrl.pathname
  const isProtectedRoute = protectedRoutes.some(route => path.startsWith(route))
  const sessionCookie = req.cookies.get('sessionid')?.value
  const hasSession = !!sessionCookie

  if (path.includes('/lastfm-callback')) {
    return NextResponse.next()
  }

  if (isProtectedRoute && !hasSession) {
    return NextResponse.redirect(new URL('/login', req.nextUrl))
  }

  if (path === '/login' && hasSession) {
    return NextResponse.redirect(new URL('/music-map', req.nextUrl))
  }

  if (path === '/') {
    if (hasSession) {
      return NextResponse.redirect(new URL('/music-map', req.nextUrl))
    }
  }

  return NextResponse.next()
}

// Routes middleware should run on
export const config = {
  matcher: [
    '/((?!api|_next/static|_next/image|favicon.ico|.*\\.png$|.*\\.jpg$|.*\\.jpeg$|.*\\.gif$|.*\\.svg$|.*\\.css$|.*\\.js$).*)',
  ],
}