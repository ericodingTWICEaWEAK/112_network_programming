#include <stdio.h>
#include <winsock.h>

#define MAXLINE 70    /* 字串緩衝區長度 */
#define BraodcastPort 5678
#define trap_num 10
#define player_num 5

SOCKET clnt_sd[5];
SOCKET Braodcast_sd;
struct sockaddr_in cli;
int cli_len;

int     trap[trap_num][3];
int     player_x[player_num];
int     player_y[player_num];

int 	player_state[player_num];

int playing = 0 ;
int game_over = 0;

struct T_Args{
    int trap_ID;
    int unopen_num;
};

int traped(int n)
{
	int i,j,trap_x,trap_y;
	for(i=0;i<trap_num;i++)
	{
		for(j=0;j<3;j++)
		{
			trap_x=300+i*200;
			trap_y=100+j*200;
			if(trap[i][j]&&(abs(trap_x-player_x[n])<=130&&abs(trap_y-player_y[n])<=130))
			{
				return 1;
			}
		}
	}
	return 0;
}

void check_player_alive()
{
	int i;
	char str[100];
	for(i=0;i<player_num;i++)
	{
		if(player_state[i]==1 && traped(i))
		{
			sprintf(str,"2%04d00000000",i);
			player_state[i]=-1;
			boardcast(str);
		}
	}
	for(i=1;playing > 1 && i<player_num;i++)
	{
		if(player_state[i]==1)
		{
			break;
		}
	}
	if(game_over == 0 && i==player_num)
	{
		//殺光光 
		printf("player0 win\n");
		sprintf(str,"6000000000000",i);
		game_over = 1;
		boardcast(str);
	}
}

void boardcast(char *str)
{
	int j;
	for(j=0;j<5;j++)
	{
		cli.sin_port = htons(BraodcastPort +j);	
		sendto(Braodcast_sd, str, strlen(str), 0,(LPSOCKADDR)&cli,cli_len);        
        //printf("server broadcast on port:%d: %s\n",BraodcastPort+j ,str);		// 顯示送去client 的字串			
	}
}

void* boardcast_all()
{
	char str[100];
	int j;
	Sleep(200);
	for(j=0;j<player_num;j++)
	{
		sprintf(str,"0%04d%04d%04d",j,player_x[j],player_y[j]);
		//printf("%s\n",str);
		boardcast(str);	
	}			
}

void* trap_action(void* t_Args)
{
	int trap_ID = ((struct T_Args *) t_Args)->trap_ID;
	int unopen_num = ((struct T_Args *) t_Args)->unopen_num;
	//printf("%d,%d\n",trap_ID,unopen_num);
	int i;
	char str[100];
	for(i=0;i<3;i++)
	{
		if(i != unopen_num)
		{
			trap[trap_ID][i]=0;
			
		}
	}
	sprintf(str,"3%04d%04d0000",trap_ID,unopen_num);
	boardcast(str);
	Sleep(1000);
	for(i=0;i<3;i++)
	{
		if(i != unopen_num)
		{
			trap[trap_ID][i]=1;
		}
	}
	sprintf(str,"4%04d%04d0000",trap_ID,unopen_num);
	boardcast(str);
	check_player_alive();
	Sleep(2000);
	for(i=0;i<3;i++)
	{
		if(i != unopen_num)
		{
			trap[trap_ID][i]=0;
		}
	}
	sprintf(str,"5%04d%04d0000",trap_ID,unopen_num);
	boardcast(str);	
}

void* check_socket_alive()
{
	int n,i;
	char tmp[100];
	while(1)
	{
		for(i=0;i<5;i++)
		{
			if(clnt_sd[i]!=-1)
			{
				n = send(clnt_sd[i],"000", 4,0);
				if(n==-1)
				{
					clnt_sd[i]=-1;
					player_state[i]=0;
					printf("Client[%d] is disconnected.\n",i);
					playing--;
					sprintf(tmp,"1%04d00000000",i);
					player_x[i]=9999;
					player_y[i]=9999;					
					boardcast(tmp);
				}					
			}
		}
		Sleep(5000);		
	}
}

void init()
{
	playing = 0;
	game_over = 0;
	int i=0;
	for(i=0;i<trap_num;i++)
  	{
  		trap[i][0]=0;
		trap[i][1]=0;
		trap[i][2]=0;
	}
	for(i=0;i<player_num;i++)
	{
		player_x[i]=9999;
		player_y[i]=9999;
		player_state[i]=0;
	}
}



int main(){
	init();
	SOCKET sd;
	
	WSADATA wsadata;
	struct sockaddr_in serv,clnt;
	int i,j,n;
	char str[100]="I love NP!";
	
	struct T_Args* t_Args[10];
	for(i=0;i<10;i++)
	{
		t_Args[i] = (struct T_Args*) malloc(sizeof(struct T_Args));		
		t_Args[i]->trap_ID=i;
		t_Args[i]->unopen_num=-1;
	}

    
	
	WSAStartup(0x101,&wsadata);
	sd = socket(AF_INET, SOCK_STREAM, 0);
	serv.sin_family = AF_INET;
	serv.sin_port = htons(1234);
	serv.sin_addr.s_addr = inet_addr("127.0.0.1");
	
	Braodcast_sd=socket(AF_INET, SOCK_DGRAM, 0);// 開啟 UDP socket
    BOOL broadcast = TRUE;
    if(	setsockopt(Braodcast_sd, SOL_SOCKET, SO_BROADCAST, (const char*)&broadcast, sizeof(broadcast))<0)
    	printf("setsockopt() error!\n"); 	
   	cli_len = sizeof(cli);
   	printf("Server starts broadcasting on port:%d\n",BraodcastPort);
   	               
    cli.sin_family      = AF_INET;
   	cli.sin_addr.s_addr = inet_addr("255.255.255.255");
   	cli.sin_port        = htons(BraodcastPort);
	
	bind(sd, (struct sockaddr *) &serv, sizeof(serv));
	
	listen(sd,5);
	
	u_long iMode=1;
	ioctlsocket(sd,FIONBIO,&iMode);
	for(i=0;i<5;i++)
	{
		clnt_sd[i]=-1;
	}
	int clnt_len=sizeof(clnt);
	printf("Server waits.\n");
	HANDLE Thread0 = CreateThread(NULL, 0, (LPTHREAD_START_ROUTINE)check_socket_alive, NULL, 0, NULL);
	while(1){
		
		// 連線區 
		memset(str,0,100);
		n =  accept(sd, (struct sockaddr *)  &clnt,&clnt_len );
		if(n!=-1)
		{
			for(i=0;i<5;i++)
			{
				if(clnt_sd[i]==-1)
				{
					if(i==0)
					{
						game_over = 0;
					}
					clnt_sd[i]=n;
					player_state[i]=1;
					printf("Client[%d] is connected.\n",i);	
					playing++;
					printf("playing: %d\n",playing);
					sprintf(str,"%d",i);
					n = send(clnt_sd[i],str, strlen(str)+1,0);
					if(n == SOCKET_ERROR)
					{
						clnt_sd[i]=-1;
						player_state[i]=0;
						printf("Client[%d] is disconnected.\n",i);
						playing--;
					}
					else
					{
						//printf("(server send to client[%d]): %s\n",i,str);
						
					}
					HANDLE Thread1 = CreateThread(NULL, 0, (LPTHREAD_START_ROUTINE)boardcast_all, NULL, 0, NULL);
					break;					
				}
			}
		}	
		// 接收TCP並廣播區 
		for(i=0;i<5;i++)
		{
			if(clnt_sd[i]!=-1)
			{
				memset(str,0,100);
				n = recv(clnt_sd[i],str, MAXLINE,0);
				if(n!=-1)
				{
					//printf("Client[%d] send:%s\n",i,str);
					if(str[0]=='0')
					{
						int ID = str[4]-'0';
						int x = (str[5]-'0') *1000 + (str[6]-'0' ) *100 + (str[7]-'0' )*10 + (str[8]-'0');
						int y = (str[9]-'0') *1000 + (str[10]-'0' ) *100 + (str[11]-'0' )*10 + (str[12]-'0');
						player_x[ID]=x;
						player_y[ID]=y;
						sprintf(str,"0%04d%04d%04d",ID,player_x[ID],player_y[ID]);
						boardcast(str);
						if(!game_over)
						{
							check_player_alive();
						}
						if(!game_over && ID!=0 && player_x[ID]>=2250)
						{
							//到終點 
							printf("player%d win\n",ID);
							sprintf(str,"6000100000000");
							game_over = 1;
							boardcast(str);
						}
					}
					if(str[0]=='1')
					{
						int ID = (str[3]-'0') *10 + str[4]-'0';
						t_Args[ID]->unopen_num = (str[5]-'0') *1000 + (str[6]-'0' ) *100 + (str[7]-'0' )*10 + (str[8]-'0');
						HANDLE Thread2 = CreateThread(NULL, 0, (LPTHREAD_START_ROUTINE)trap_action, t_Args[ID], 0, NULL);
					}
				}
			}
		}
	}
	// 關閉 
	closesocket(Braodcast_sd);
	closesocket(sd);
	for(i=0;i<5;i++)
	{
		closesocket(clnt_sd[i]);
	}
	WSACleanup();
	system("pause");
	
}
