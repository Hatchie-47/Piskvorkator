FOR /L %%X IN (1,1,10) DO (
docker run -d --name player%%X --restart unless-stopped dockerator:01.11.01
)