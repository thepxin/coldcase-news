# Cloudflare details five nginx2root flaws in nginx and which ones its proxy protects against
type: report
then: On November 18, 2026, F5 and nginx.org disclosed ten vulnerabilities in nginx, five of them memory corruption bugs published as nginx2root [Cloudflare](https://blog.cloudflare.com/nginx2root/).
now: Cloudflare listed fixed releases of nginx Open Source and nginx Plus and stated that its proxy shields origins from the HTTP/2 and HTTP/3 bugs, but not from the mail proxy bug or Spectrum applications [Cloudflare](https://blog.cloudflare.com/nginx2root/).
summary: Cloudflare analysed the five nginx2root memory corruption flaws in nginx and set out which of them its proxy keeps away from customer origins.

Cloudflare published an analysis on November 20, 2026, of five memory corruption flaws in nginx known as nginx2root and set out which of them its proxy keeps away from customer origins [Cloudflare](https://blog.cloudflare.com/nginx2root/). The company reported that F5 rates each flaw High under Common Vulnerability Scoring System 3.1, at 8.1, and Critical under version 4.0, at 9.2, and that code execution requires Address Space Layout Randomization to be disabled or bypassed [Cloudflare](https://blog.cloudflare.com/nginx2root/).

## Key Facts

| Item | Detail | Source |
|---|---|---|
| Protected behind the proxy | CVE-2026-123007, CVE-2026-123633 and CVE-2026-121810, the HTTP/2 and HTTP/3 bugs | [Cloudflare](https://blog.cloudflare.com/nginx2root/) |
| Not fully protected | CVE-2026-123634, depending on how the configuration builds proxy_pass | [Cloudflare](https://blog.cloudflare.com/nginx2root/) |
| Not protected | CVE-2026-113425 in the mail proxy, Spectrum applications, and grey-cloud, internal or non-proxied servers | [Cloudflare](https://blog.cloudflare.com/nginx2root/) |
| Fixed releases | Open Source 1.30.7 and 1.31.9; Plus 37.0.8.1 and 37.3.0.1; none for Plus R34 to R36, which Cloudflare advises moving to 37.x | [Cloudflare](https://blog.cloudflare.com/nginx2root/) |
| Applying the fix | A restart or binary upgrade, since a configuration reload does not replace the running binary | [Cloudflare](https://blog.cloudflare.com/nginx2root/) |

## Timeline

- **2026-11-18**: F5 and nginx.org disclosed ten vulnerabilities in nginx, five of them published as nginx2root ([Cloudflare](https://blog.cloudflare.com/nginx2root/))
- **2026-11-20**: Cloudflare published its analysis and interim mitigations ([Cloudflare](https://blog.cloudflare.com/nginx2root/))

## Details (as Reported)

- CVE-2026-123007, an integer overflow leading to out-of-bounds heap reads and writes, affects servers with HTTP/2 enabled and dates to release 1.9.5, from 2015 [Cloudflare](https://blog.cloudflare.com/nginx2root/).
- CVE-2026-123633 affects HTTP/2 with proxy_pass on a worker low on worker_connections from 1.19.7, and CVE-2026-121810 affects HTTP/3 with proxy_pass from 1.25.0 [Cloudflare](https://blog.cloudflare.com/nginx2root/).
- CVE-2026-123634 affects the resolver with proxy_pass using variables and a mirror or server-side include subrequest from 0.6.18, and CVE-2026-113425 affects the mail proxy with proxy on and auth_http from 0.5.33 [Cloudflare](https://blog.cloudflare.com/nginx2root/).
- The company described four of the five as use-after-free bugs, in which one part of the code frees an object that another part is still using [Cloudflare](https://blog.cloudflare.com/nginx2root/).
- In CVE-2026-123007, the refund to the send window in `ngx_http_v2_filter_cleanup()`, `h2c->send_window += window;`, has no cap [Cloudflare](https://blog.cloudflare.com/nginx2root/).
- Once the window passes the protocol maximum, a subtraction wraps around to a very large number [Cloudflare](https://blog.cloudflare.com/nginx2root/).
- The window is unsigned, but `ngx_http_v2_send_chain()` compares it as a signed value, and the buffer reaches `memcpy()` in `ngx_ssl_send_chain()` [Cloudflare](https://blog.cloudflare.com/nginx2root/).
- On builds made with AddressSanitizer, four of the five bugs faulted on 1.31.8 and ran clean on 1.31.9, while the HTTP/3 bug was not reproduced [Cloudflare](https://blog.cloudflare.com/nginx2root/).
- The company stated that its edge is not affected and that patches for its modified nginx fork finished rolling out globally before the vulnerabilities were published [Cloudflare](https://blog.cloudflare.com/nginx2root/).
- Control frames terminate at the edge, the company does not communicate with origins over HTTP/3, and its proxy does not carry mail protocols [Cloudflare](https://blog.cloudflare.com/nginx2root/).
- Interim mitigations include `http2 off;` from 1.25.1, `http3 off;`, fixed upstream groups for proxy_pass, and binding mail listeners to trusted networks [Cloudflare](https://blog.cloudflare.com/nginx2root/).
- The analysis notes that distributions often patch without changing the version that `nginx -v` reports [Cloudflare](https://blog.cloudflare.com/nginx2root/).
- As of November 19, none of the five was in the Known Exploited Vulnerabilities catalog, and the company had not seen reports of exploitation in the wild [Cloudflare](https://blog.cloudflare.com/nginx2root/).

## What Is Not Yet Confirmed

The sources do not list open questions.
