/* Temporary serial file transfer for a running recovery Linux.
 * No flash operations. Put is restricted to /tmp/. Protocol matches the
 * RAM loader's LE magic/length/CRC header, with a 0x55 sync byte first.
 */
#define _DEFAULT_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <poll.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <termios.h>
#include <unistd.h>

static uint32_t crc(uint32_t c, const unsigned char *p, size_t n)
{
 while (n--) {
  c ^= *p++;
  for (int i = 0; i < 8; i++) c = (c >> 1) ^ (0xedb88320u & -(c & 1));
 }
 return c;
}

static int io(int fd, void *buf, size_t n, int writing)
{
 unsigned char *p = buf;
 while (n) {
  struct pollfd wait = { .fd = fd, .events = writing ? POLLOUT : POLLIN };
  int r = poll(&wait, 1, 15000);
  if (r < 0 && errno == EINTR) continue;
  if (r <= 0) return -1;
  ssize_t got = writing ? write(fd, p, n) : read(fd, p, n);
  if (got < 0 && errno == EINTR) continue;
  if (got <= 0) return -1;
  p += got;
  n -= got;
 }
 return 0;
}

static uint32_t word(const unsigned char *p)
{
 return (uint32_t)p[0] | (uint32_t)p[1] << 8 | (uint32_t)p[2] << 16 | (uint32_t)p[3] << 24;
}

static void setword(unsigned char *p, uint32_t v)
{
 for (int i = 0; i < 4; i++) p[i] = v >> (8 * i);
}

int main(int argc, char **argv)
{
 if (argc < 3 || (strcmp(argv[1], "put") && strcmp(argv[1], "get"))) {
  fprintf(stderr, "usage: serial-file put|get path [tty]\n");
  return 2;
 }
 int put = !strcmp(argv[1], "put");
 if (put && strncmp(argv[2], "/tmp/", 5)) return 2;
 int fd = open(argv[2], put ? O_WRONLY | O_CREAT | O_EXCL : O_RDONLY, 0600);
 if (fd < 0) { perror("open file"); return 2; }
 int tty = open(argc > 3 ? argv[3] : "/dev/console", O_RDWR | O_NOCTTY);
 struct termios original, raw;
 if (tty < 0 || tcgetattr(tty, &original)) { perror("open tty"); close(fd); return 2; }
 raw = original;
 cfmakeraw(&raw);
 cfsetspeed(&raw, B500000);
 if (tcsetattr(tty, TCSADRAIN, &raw)) { perror("set tty"); close(fd); close(tty); return 2; }
 int good = 0;
 unsigned char sync, h[12], buf[16384];
 uint32_t sum = ~0u, expected, length, remaining;
 if (io(tty, &sync, 1, 0) || sync != 0x55) goto done;
 if (io(tty, "FEMTO-LINUX-READY\r\n", 19, 1)) goto done;
 if (put) {
  if (io(tty, h, sizeof(h), 0) || word(h) != 0x314d5446) goto done;
  length = word(h + 4);
  expected = word(h + 8);
  if (!length || length > 32u * 1024 * 1024) goto done;
  remaining = length;
  while (remaining) {
   size_t n = remaining < sizeof(buf) ? remaining : sizeof(buf);
   if (io(tty, buf, n, 0) || io(fd, buf, n, 1)) goto done;
   sum = crc(sum, buf, n);
   remaining -= n;
  }
  if (~sum != expected || fsync(fd)) goto done;
 } else {
  struct stat st;
  if (fstat(fd, &st) || st.st_size <= 0 || st.st_size > 512 * 1024 * 1024) goto done;
  length = st.st_size;
  remaining = length;
  while (remaining) {
   size_t n = remaining < sizeof(buf) ? remaining : sizeof(buf);
   if (io(fd, buf, n, 0)) goto done;
   sum = crc(sum, buf, n);
   remaining -= n;
  }
  if (lseek(fd, 0, SEEK_SET) != 0) goto done;
  setword(h, 0x314d5446);
  setword(h + 4, length);
  setword(h + 8, ~sum);
  if (io(tty, h, sizeof(h), 1)) goto done;
  remaining = length;
  while (remaining) {
   size_t n = remaining < sizeof(buf) ? remaining : sizeof(buf);
   if (io(fd, buf, n, 0) || io(tty, buf, n, 1)) goto done;
   remaining -= n;
  }
  if (io(tty, &sync, 1, 0) || sync != 6) goto done;
 }
 good = 1;
done:
 close(fd);
 if (put && !good) unlink(argv[2]);
 const char *status = good ? "\r\nFEMTO-LINUX-OK\r\n" : "\r\nFEMTO-LINUX-BAD\r\n";
 io(tty, (void *)status, strlen(status), 1);
 tcdrain(tty);
 usleep(200000);
 tcsetattr(tty, TCSADRAIN, &original);
 close(tty);
 return !good;
}
