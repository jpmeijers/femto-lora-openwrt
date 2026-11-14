/* Read-only data+OOB backup through MEMREAD, without MTDFILEMODE.
 * Useful for the MT7620 driver, which supports raw reads but not OOB writes.
 */
#include <errno.h>
#include <fcntl.h>
#include <mtd/mtd-user.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/ioctl.h>
#include <unistd.h>

int main(int argc, char **argv)
{
 if (argc < 3 || argc > 5) { fprintf(stderr, "usage: rawdump /dev/mtdN /tmp/output [length [start]]\n"); return 2; }
 int fd = open(argv[1], O_RDONLY);
 struct mtd_info_user info;
 if (fd < 0 || ioctl(fd, MEMGETINFO, &info)) { perror("MTD info"); return 1; }
 if (info.type != MTD_NANDFLASH || info.writesize != 2048 || info.oobsize != 64) return 2;
 uint64_t length = argc >= 4 ? strtoull(argv[3], NULL, 0) : info.size;
 uint64_t start = argc == 5 ? strtoull(argv[4], NULL, 0) : 0;
 if (!length || start + length > info.size || length % 2048 || start % 2048) return 2;
 int output = open(argv[2], O_WRONLY | O_CREAT | O_EXCL, 0600);
 if (output < 0) { perror("output"); return 1; }
 unsigned char page[2112];
 for (uint64_t offset = start; offset < start + length; offset += 2048) {
  struct mtd_read_req req = {
   .start = offset, .len = 2048, .ooblen = 64,
   .usr_data = (uintptr_t)page, .usr_oob = (uintptr_t)(page + 2048),
   .mode = MTD_OPS_RAW,
  };
  if (ioctl(fd, MEMREAD, &req)) { perror("MEMREAD"); return 1; }
  size_t done = 0;
  while (done < sizeof(page)) {
   ssize_t n = write(output, page + done, sizeof(page) - done);
   if (n < 0 && errno == EINTR) continue;
   if (n <= 0) { perror("write backup"); return 1; }
   done += n;
  }
 }
 if (close(output)) return 1;
 close(fd);
 return 0;
}
