#-*- coding:cp949 -*-
from werewolf.database.DATABASE import DATABASE
from werewolf.game.GAME_STATE import GAME_STATE
from werewolf.game.entry.Entry import Truecharacter
from werewolf.game.entry.Entry import Race
import random
import copy

class Rule:
    def __init__(self,game):
        self.game = game

class WerewolfRule(Rule):
    def nextTurn(self):
        if(self.game.state== GAME_STATE.READY):
            if(self.min_players <= self.game.players and self.game.players <= self.max_players):
                print "���� �ʱ�ȭ ����"
                self.initGame()                
            else:
                pass
                self.game.deleteGame()
        elif(self.game.state==GAME_STATE.PLAYING):
            if(self.game.day == 1):
                self.nexeTurn_2day()
            else:
                self.nextTurn_Xday()
            
    def initGame(self):       
        #�÷����غ� ���
        expertPlayers = self.game.entry.getExpertPlayers()
        #print "expertPlayers",expertPlayers

        #�ʺ���
        novicePlayers = self.game.entry.getNovicePlayers()
        #print "novicePlayers",novicePlayers

        truecharacterList = copy.copy(self.temp_truecharacter[len(novicePlayers) + len(expertPlayers)+1 ])
        print "players",len(novicePlayers) + len(expertPlayers)+1
        #���� ��� ��ġ
        while(len(novicePlayers)>0):
            #print "len(novicePlayers)",len(novicePlayers)
            #print "truecharacterList",truecharacterList
            if(truecharacterList[0] != Truecharacter.HUMAN):
                break
            ram = random.randrange(0,len(novicePlayers))
            #print "random",ram
            player = novicePlayers.pop()
            job = truecharacterList.pop(0)            
            #print "player: ",player.id,"job: ",job
            player.setTruecharacter(job)

        restPlayers =expertPlayers + novicePlayers
        #print "restEntry:", restPlayers
        #print "restJob:", truecharacterList
        
        #���� ���� ��ġ
        while(len(restPlayers)>0):
            player = restPlayers.pop(0)
            job = truecharacterList.pop(random.randrange(0,len(truecharacterList))  )            
            #print "player: ",player.id,"job: ",job
            player.setTruecharacter(job)
            
        #2. ������� �ڸ�Ʈ
        victim =self.game.entry.getVictim()
        #print "victim",victim
        victim.writeWill()

        #3. ���� ���� ������Ʈ
        self.game.setGameState("state",GAME_STATE.PLAYING)
        self.game.setGameState("day",self.game.day+1)
        
        #���� ������..
        cursor = self.game.db.cursor
        query = "update `zetyx_board_werewolf` set `%s` = '%s'  where no = '%s'"
        query%=("is_secret",0,self.game.game)
        #print query
        cursor.execute(query) 
        
        #4. �ڸ�Ʈ �ʱ�ȭ
        self.game.entry.initComment()

    def decideByMajority(self):
        cursor = self.game.db.cursor
        
        print "��ǥ!"
        alivePlayers = self.game.entry.getAliveEntry()
                
        #��� �ִ� ����� 1�� �̻��� ��쿡�� ��ǥ�� �����Ѵ�.
        if(len(alivePlayers)<=1 ): return
        #��� ������� ��ǥ�� �����ߴ��� Ȯ���Ѵ�.
        for alivePlayer in alivePlayers:
            #��ǥ�� ���ߴٸ�! ���� ��ǥ ����     
            if alivePlayer.hasVoted() is False:
                alivePlayer.voteRandom(alivePlayers)
        
        #���� ǥ�� ���� ���� ����� ã�´�.
        query = '''select `candidacy`, count(*) as count from `zetyx_board_werewolf_vote` 
        where game = '%s' and day ='%s' 
        group by `candidacy` 
        order by `count`  DESC '''
        query%=(self.game.game,self.game.day)
        #print query
        
        cursor.execute(query)
        result = cursor.fetchall()
        #print result
        
        count = 0
        candidacy_list=[]
        
        for temp in result :
            if count <= temp['count']: 
                count =temp['count']
                #print "count", count
            else:
                break
            candidacy_list.append(temp['candidacy'])
            
        return self.game.entry.getCharacter(candidacy_list[random.randrange(0,len(candidacy_list))])   
   
    def decideByWerewolf(self):
        cursor = self.game.db.cursor
        
        print "����!!"
        #������ ������...
        humanRace = self.game.entry.getEntryByRace(Race.HUMAN)
        #print alivePlayers

        #������!
        werewolfPlayers = self.game.entry.getPlayersByTruecharacter(Truecharacter.WEREWOLF,"('����')")
        #print werewolfPlayers 
        
        #��� �ִ� �ζ��� ���� ���� ������ �����Ѵ�.
        if(len(werewolfPlayers) ==0 ): 
            return        

        #�ζ����� ������ �����ߴ��� Ȯ���Ѵ�.
        for werewolfPlayer in werewolfPlayers:
            #������ ���ߴٸ�! ���� ���� ����     
            if werewolfPlayer.hasAssault() is False:
                werewolfPlayer.assaultRandom(humanRace )


        #�ζ����� ���� �����ϴ� ����� ã�´�.
        query = '''select `injured`, count(*) as count from `zetyx_board_werewolf_deathNote` 
        where game = '%s' and day ='%s' 
        group by `injured` 
        order by `count`  DESC '''
        query%=(self.game.game,self.game.day)
        #print query
        
        cursor.execute(query)
        result = cursor.fetchall()
        #print result
        
        count = 0
        injured_list=[]
        
        for temp in result :
            if count <= temp['count']: 
                count =temp['count']
                #print "count", count
            else:
                break
            injured_list.append(temp['injured'])
        #print injured_list[random.randrange(0,len(injured_list))],injured_list
        return self.game.entry.getCharacter(injured_list[random.randrange(0,len(injured_list))])
           
class BasicRule(WerewolfRule):
    min_players = 11
    max_players  = 16
    
    # �⺻ ����
    temp_truecharacter ={}
    temp_truecharacter[11] =  [1,1,1,1,2,3,4,5,5,6]
    temp_truecharacter[12] =  [1,1,1,1,1,2,3,4,5,5,6]
    temp_truecharacter[13] =  [1,1,1,1,1,1,2,3,4,5,5,6]
    temp_truecharacter[14] =  [1,1,1,1,1,1,1,2,3,4,5,5,6]
    temp_truecharacter[15] =  [1,1,1,1,1,1,1,2,3,4,5,5,5,6]
    temp_truecharacter[16] =  [1,1,1,1,1,1,2,3,4,5,5,5,6,7,7]    

    def __init__(self,game):
        WerewolfRule.__init__(self, game)
        #print "basicRule"    
    def initGame(self):
        print "init Basic Rule"
        WerewolfRule.initGame(self)
    def nexeTurn_2day(self):
        print "2��°�� ���!"

        #�Ϲ� �α׸� ���� ���� ����� üũ�Ѵ�.
        self.game.entry.checkNoCommentPlayer()

        #����� NPC ����
        victim =self.game.entry.getVictim()
        victim.toDeathByWerewolf()

        #������ ��Ŵ 
        noMannerPlayers = self.game.entry.getNoMannerPlayers()
        for noMannerPlayer in noMannerPlayers:
            noMannerPlayer.toDeath("���� ")       
        
        #�ڸ��� �ʱ�ȭ
        self.game.entry.initComment()

        #3. ���� ���� ������Ʈ
        self.game.setGameState("state","������")
        self.game.setGameState("day",self.game.day+1)

    def nextTurn_Xday(self):
        print "���� ���� ���!"                
        #�Ϲ� �α׸� ���� ���� ����� üũ�Ѵ�.
        self.game.entry.checkNoCommentPlayer()
        
        #��ǥ -��� �ִ� �����ڰ� ��ǥ�� �ߴ��� üũ, ���ߴٸ� ���� ��ǥ
        victim = self.decideByMajority()
        if victim:
            victim.toDeath("����") 
        
        #������ ��Ŵ 
        noMannerPlayers = self.game.entry.getNoMannerPlayers()
        for noMannerPlayer in noMannerPlayers:
            noMannerPlayer.toDeath("���� ")       
        
        #�ڸ��� �ʱ�ȭ
        self.game.entry.initComment()
        
        #����!
        assaultVictim = self.decideByWerewolf()
        if assaultVictim:
            #print "assaultVictim",assaultVictim
            self.assaultByWerewolf(assaultVictim,victim)
            
        #���� ���� Ȯ��
        #���!
        humanRace = self.game.entry.getEntryByRace(Race.HUMAN)
        #for human in humanRace :
        #    print human
        
        #������!
        werewolfRace = self.game.entry.getEntryByRace(Race.WEREWOLF)
        #for werewolf in werewolfRace :
        #    print werewolf
        
        if((len(humanRace) <= len(werewolfRace)) or (len(humanRace) == 0)):
            print "�ζ� �¸�"
            self.game.setGameState("win","1")
            if(self.game.termOfDay == 60):
                self.game.setGameState("state",GAME_STATE.TESTOVER)
            else:
                self.game.setGameState("state",GAME_STATE.GAMEOVER)
            
        elif(len(werewolfRace) == 0):
            print "�ΰ� �¸�"
            self.game.setGameState("win","0")
            if(self.game.termOfDay == 60):
                self.game.setGameState("state",GAME_STATE.TESTOVER)
            else:
                self.game.setGameState("state",GAME_STATE.GAMEOVER)
        else:
            print "��� ����"
            #self.game.setGameState("state","������")
        
        self.game.setGameState("day",self.game.day+1)

    def assaultByWerewolf(self,assaultVictim,victim):
        self.game.entry.recordAssaultResult(assaultVictim)
            
        guard={}
        hunterPlayer = self.game.entry.getPlayersByTruecharacter(Truecharacter.BODYGUARD)[0]    

        if(hunterPlayer.alive == "����"):
            #print "hunterPlayer",hunterPlayer        
            guard = hunterPlayer.guard()
            if guard is not None:
                guard = self.game.entry.getCharacter(guard['purpose'])
                #print "guard", guard
                
        if assaultVictim.id == victim.id:
            #print "���� ����: (�����)"
            pass
        elif guard and assaultVictim.id == guard.id:
            #print "���� ����: (����)" 
            pass
        else:
            #print "���� ����", assaultVictim
            assaultVictim.toDeath("����")       

        #print "guard: ",guard
        #print "assaultVictim: ", assaultVictim
        #print "victim: ", victim        

class HamsterRule(BasicRule):
    min_players = 11
    max_players = 17
    
    # �⺻ ����
    temp_truecharacter ={}
    temp_truecharacter[11] =  [1,1,1,1,2,3,4,5,5,6]
    temp_truecharacter[12] =  [1,1,1,1,1,2,3,4,5,5,6]
    temp_truecharacter[13] =  [1,1,1,1,1,1,2,3,4,5,5,6]
    temp_truecharacter[14] =  [1,1,1,1,1,1,1,2,3,4,5,5,6]
    temp_truecharacter[15] =  [1,1,1,1,1,1,1,2,3,4,5,5,5,6]
    temp_truecharacter[16] =  [1,1,1,1,1,1,2,3,4,5,5,5,6,7,7]    
    temp_truecharacter[17] =  [1,1,1,1,1,1,2,3,4,5,5,5,6,7,7,8]    

    def __init__(self,game):
        WerewolfRule.__init__(self, game)
        #print "Hamster Rule"

    def nextTurn(self):
        if(self.game.state== GAME_STATE.READY):
            if(self.min_players <= self.game.players and self.game.players <= self.max_players):
                print "���� �ʱ�ȭ ����"
                self.initGame()                
            else:
                pass
                self.game.deleteGame()
        elif(self.game.state==GAME_STATE.PLAYING):
            if(self.game.day == 1):
                if(self.game.players == 17):
                    self.nexeTurn_2day()                    
                else:
                    BasicRule.nexeTurn_2day(self)        
            else:
                if(self.game.players == 17):
                    self.nextTurn_Xday()
                else:
                    BasicRule.nextTurn_Xday(self)        

    def initGame(self):
        print "initHamster!!"
        WerewolfRule.initGame(self)        
    def nexeTurn_2day(self):
        print "2��°�� ���!"

        #�Ϲ� �α׸� ���� ���� ����� üũ�Ѵ�.
        self.game.entry.checkNoCommentPlayer()

        #����� NPC ����
        victim =self.game.entry.getVictim()
        victim.toDeathByWerewolf()
        
        #�ܽ���
        hamsterPlayer = self.game.entry.getPlayersByTruecharacter(Truecharacter.WEREHAMSTER)[0] 
        
        #�� ��!
        self.assaultByForecast(hamsterPlayer)

        #������ ��Ŵ 
        noMannerPlayers = self.game.entry.getNoMannerPlayers()
        for noMannerPlayer in noMannerPlayers:
            noMannerPlayer.toDeath("���� ")       
        
        #�ڸ��� �ʱ�ȭ
        self.game.entry.initComment()

        #3. ���� ���� ������Ʈ
        self.game.setGameState("state","������")
        self.game.setGameState("day",self.game.day+1)
                    
    def nextTurn_Xday(self):
        print "���� ���� ���!"                
        #�Ϲ� �α׸� ���� ���� ����� üũ�Ѵ�.
        self.game.entry.checkNoCommentPlayer()
        
        #��ǥ -��� �ִ� �����ڰ� ��ǥ�� �ߴ��� üũ, ���ߴٸ� ���� ��ǥ
        victim = self.decideByMajority()
        if victim:
            victim.toDeath("����") 
        
        #������ ��Ŵ 
        noMannerPlayers = self.game.entry.getNoMannerPlayers()
        for noMannerPlayer in noMannerPlayers:
            noMannerPlayer.toDeath("���� ")       
        
        #�ڸ��� �ʱ�ȭ
        self.game.entry.initComment()

        #�ܽ���
        hamsterPlayer = self.game.entry.getPlayersByTruecharacter(Truecharacter.WEREHAMSTER)[0] 
        
        #�� ��!
        self.assaultByForecast(hamsterPlayer)

        #����!
        assaultVictim = self.decideByWerewolf()
        if assaultVictim:
            #print "assaultVictim",assaultVictim
            self.assaultByWerewolfAndHamster(assaultVictim,victim,hamsterPlayer)
            
        #���� ���� Ȯ��
        #���!
        humanRace = self.game.entry.getEntryByRace(Race.HUMAN)
        #for human in humanRace :
        #    print human
        
        #������!
        werewolfRace = self.game.entry.getEntryByRace(Race.WEREWOLF)
        #for werewolf in werewolfRace :
        #    print werewolf
        
        if((len(humanRace) <= len(werewolfRace)) or (len(humanRace) == 0)):
            if(self.game.termOfDay == 60):
                self.game.setGameState("state",GAME_STATE.TESTOVER)
            else:
                self.game.setGameState("state",GAME_STATE.GAMEOVER)

            if hamsterPlayer.alive == "����" :
                print "�ܽ��� �¸�"
                self.game.setGameState("win","2")
            else:
                print "�ζ� �¸�"
                self.game.setGameState("win","1")
            
        elif(len(werewolfRace) == 0):
            if(self.game.termOfDay == 60):
                self.game.setGameState("state",GAME_STATE.TESTOVER)
            else:
                self.game.setGameState("state",GAME_STATE.GAMEOVER)

            if hamsterPlayer.alive == "����" :
                print "�ܽ��� �¸�"
                self.game.setGameState("win","2")
            else:
                print "�ΰ� �¸�"            
                self.game.setGameState("win","0")
        else:
            print "��� ����"
            #self.game.setGameState("state","������")
        
        self.game.setGameState("day",self.game.day+1)
        
    def assaultByForecast(self,hamsterPlayer):
        #print "����!!"
        forecastTarget={}
        seerPlayer = self.game.entry.getPlayersByTruecharacter(Truecharacter.SEER)[0]    

        if(seerPlayer.alive == "����"):
            #print "seerPlayer",seerPlayer        
            forecastTarget = seerPlayer.openEye()
            #print "forecastTarget", forecastTarget
                    
            if forecastTarget is not None:
                forecastTarget = self.game.entry.getCharacter(forecastTarget['mystery'])
                #print "forecastTarget", forecastTarget  

        #print "hamsterPlayer",hamsterPlayer   

        if(forecastTarget and hamsterPlayer.alive =="����" and hamsterPlayer.id == forecastTarget.id):
            #print "�� ����  ����", hamsterPlayer
            hamsterPlayer.toDeath("����")                        
        else:
            #print "�� ���� ����: " 
	    pass
            
    def assaultByWerewolfAndHamster(self,assaultVictim,victim,hamsterPlayer):
        self.game.entry.recordAssaultResult(assaultVictim)
            
        guard={}
        hunterPlayer = self.game.entry.getPlayersByTruecharacter(Truecharacter.BODYGUARD)[0]    

        if(hunterPlayer.alive == "����"):
            #print "hunterPlayer",hunterPlayer        
            guard = hunterPlayer.guard()
            if guard is not None:
                guard = self.game.entry.getCharacter(guard['purpose'])
                #print "guard", guard
                
        if assaultVictim.id == victim.id:
            #print "���� ����: (�����)"
            pass
        elif guard and assaultVictim.id == guard.id:
            #print "���� ����: (����)"
            pass
        elif assaultVictim.id == hamsterPlayer.id:
            #print "���� ����: (�ܽ�)"
	        pass
        else:
            #print "���� ����", assaultVictim
            assaultVictim.toDeath("����")       

        #print "guard: ",guard
        #print "assaultVictim: ", assaultVictim
        #print "victim: ", victim              

class ExpansionRule(WerewolfRule):
    min_players = 9
    max_players  = 17
    
    # �⺻ ����
    temp_truecharacter ={}
    temp_truecharacter[9] =  [2,3,6,11,15,4,5,9]
    temp_truecharacter[10] =  [1,2,3,6,11,12,4,5,9]
    temp_truecharacter[11] =  [1,1,15,2,3,6,13,4,5,10]
    temp_truecharacter[12] =  [1,1,1,1,2,3,6,13,4,5,10]
    temp_truecharacter[13] =  [1,15,2,3,6,11,12,13,4,5,9,10]
    temp_truecharacter[14] =  [1,1,1,2,3,6,11,12,13,4,5,9,10]
    temp_truecharacter[15] =  [1,1,15,2,3,6,11,12,13,4,5,5,9,10]
    temp_truecharacter[16] =  [1,1,1,1,2,3,6,11,12,13,4,5,5,9,10]
    temp_truecharacter[17] =  [1,1,1,1,2,3,6,11,12,13,4,5,5,9,10,14]

    def __init__(self,game):
        WerewolfRule.__init__(self, game)
        #print "ExpansionRule"    
    def initGame(self):
        print "init Expansion Rule"
        WerewolfRule.initGame(self)
    def nexeTurn_2day(self):
        print "2��°�� ���!"

        #�Ϲ� �α׸� ���� ���� ����� üũ�Ѵ�.
        self.game.entry.checkNoCommentPlayer()

        #����� NPC ����
        victim =self.game.entry.getVictim()
        victim.toDeathByWerewolf()

        #������ ��Ŵ 
        noMannerPlayers = self.game.entry.getNoMannerPlayers()
        for noMannerPlayer in noMannerPlayers:
            noMannerPlayer.toDeath("���� ")       
        
        #�ڸ��� �ʱ�ȭ
        self.game.entry.initComment()

        #3. ���� ���� ������Ʈ
        self.game.setGameState("state","������")
        self.game.setGameState("day",self.game.day+1)

    def nextTurn_Xday(self):
        print "���� ���� ���!"                
        #�Ϲ� �α׸� ���� ���� ����� üũ�Ѵ�.
        self.game.entry.checkNoCommentPlayer()
        
        #��ǥ -��� �ִ� �����ڰ� ��ǥ�� �ߴ��� üũ, ���ߴٸ� ���� ��ǥ
        victim = self.decideByMajority()
        if victim:
		if victim.truecharacter == Truecharacter.DIABLO:
			if victim.awaken():
				self.game.setGameState("win","3")
			        if(self.game.termOfDay == 60):
			                self.game.setGameState("state",GAME_STATE.TESTOVER)
				else:
			                self.game.setGameState("state",GAME_STATE.GAMEOVER)
				
				self.game.setGameState("day",self.game.day+1)
				return
		victim.toDeath("����") 
        
        #������ ��Ŵ 
        noMannerPlayers = self.game.entry.getNoMannerPlayers()
        for noMannerPlayer in noMannerPlayers:
            noMannerPlayer.toDeath("���� ")       
        
        #�ڸ��� �ʱ�ȭ
        self.game.entry.initComment()
        
        #����!
        assaultVictim = self.decideByWerewolf()
        if assaultVictim:
            #print "assaultVictim",assaultVictim
            self.assaultByWerewolf(assaultVictim,victim)
            
        #���� ���� Ȯ��
        #���!
        humanRace = self.game.entry.getEntryByRace(Race.HUMAN)
        #for human in humanRace :
        #    print human
        
        #������!
        werewolfRace = self.game.entry.getEntryByRace(Race.WEREWOLF)
        #for werewolf in werewolfRace :
        #    print werewolf
        
        if((len(humanRace) <= len(werewolfRace)) or (len(humanRace) == 0)):
            print "�ζ� �¸�"
            self.game.setGameState("win","1")
            if(self.game.termOfDay == 60):
                self.game.setGameState("state",GAME_STATE.TESTOVER)
            else:
                self.game.setGameState("state",GAME_STATE.GAMEOVER)
            
        elif(len(werewolfRace) == 0):
            print "�ΰ� �¸�"
            self.game.setGameState("win","0")
            if(self.game.termOfDay == 60):
                self.game.setGameState("state",GAME_STATE.TESTOVER)
            else:
                self.game.setGameState("state",GAME_STATE.GAMEOVER)
        else:
            print "��� ����"
            #self.game.setGameState("state","������")
        
        self.game.setGameState("day",self.game.day+1)

    def assaultByWerewolf(self,assaultVictim,victim):
        self.game.entry.recordAssaultResult(assaultVictim)
            
        guard={}
        hunterPlayer = self.game.entry.getPlayersByTruecharacter(Truecharacter.BODYGUARD)[0]    

        if(hunterPlayer.alive == "����"):
            #print "hunterPlayer",hunterPlayer        
            guard = hunterPlayer.guard()
            if guard is not None:
                guard = self.game.entry.getCharacter(guard['purpose'])
                #print "guard", guard
                
        
        if assaultVictim.id == victim.id:
            #print "���� ����: (�����)"
            pass
        elif guard and assaultVictim.id == guard.id:
            #print "���� ����: " 
	        pass
        else:
            #print "���� ����", assaultVictim
            assaultVictim.toDeath("����")       

        #print "guard: ",guard
        #print "assaultVictim: ", assaultVictim
        #print "victim: ", victim     

    def decideByWerewolf(self):
        cursor = self.game.db.cursor
        
        #print "����!!"
        #������ ������...
        humanRace = self.game.entry.getEntryByRace(Race.HUMAN)
        #print alivePlayers

        #������!
        werewolfPlayers = self.game.entry.getPlayersByTruecharacter(Truecharacter.WEREWOLF,"('����')")
        readerwerewolfPlayer = self.game.entry.getPlayersByTruecharacter(Truecharacter.READERWEREWOLF)
        lonelywerewolfPlayer = self.game.entry.getPlayersByTruecharacter(Truecharacter.LONELYWEREWOLF)
        #print werewolfPlayers 
	
	if(readerwerewolfPlayer):
		readerwerewolfPlayer = readerwerewolfPlayer[0]

	if(lonelywerewolfPlayer):
		lonelywerewolfPlayer = lonelywerewolfPlayer[0]
        
        #��� �ִ� �ζ��� ���� ���� ������ �����Ѵ�.
        if(len(werewolfPlayers)==0 and (not readerwerewolfPlayer or readerwerewolfPlayer.alive=="���") and (not lonelywerewolfPlayer or lonelywerewolfPlayer.alive =="���")): 
            return        

        #�ζ����� ������ �����ߴ��� Ȯ���Ѵ�.
	if(len(werewolfPlayers)>0):
	        for werewolfPlayer in werewolfPlayers:
		    #������ ���ߴٸ�! ���� ���� ����     
	            if werewolfPlayer.hasAssault() is False:
		        werewolfPlayer.assaultRandom(humanRace )

        #�ζ����� ������ �����ߴ��� Ȯ���Ѵ�.
	if(readerwerewolfPlayer and readerwerewolfPlayer.alive=="����"):
	    #������ ���ߴٸ�! ���� ���� ����     
            if readerwerewolfPlayer.hasAssault() is False:
	        readerwerewolfPlayer.assaultRandom(humanRace )

        #�ζ����� ������ �����ߴ��� Ȯ���Ѵ�.
	if(lonelywerewolfPlayer and lonelywerewolfPlayer.alive=="����"):
	    #������ ���ߴٸ�! ���� ���� ����     
            if lonelywerewolfPlayer.hasAssault() is False:
	        lonelywerewolfPlayer.assaultRandom(humanRace )

        #�ζ����� ���� �����ϴ� ����� ã�´�.
        query = '''select `injured`, count(*)*2 as count from `zetyx_board_werewolf_deathNote` 
        where game = '%s' and day ='%s' 
        group by `injured` 
        order by `count`  DESC '''
        query%=(self.game.game,self.game.day)
        #print query
        
        cursor.execute(query)
        result = cursor.fetchall()
        #print result

	if(lonelywerewolfPlayer and lonelywerewolfPlayer.alive=="����"):
	        query = '''select `injured`, count(*) as count from `zetyx_board_werewolf_deathnotehalf` 
	        where game = '%s' and day ='%s' 
	        group by `injured` 
	        order by `count`  DESC '''
	        query%=(self.game.game,self.game.day)
	        #print query
        
		cursor.execute(query)
	        result2 = cursor.fetchall()
	        #print result2

		if(len(result)>0):
			result2 = result2[0]
			resultList =[]
			for temp in result :
				if(temp['injured'] == result2['injured']):
					temp['count']+=1
				resultList.append(temp)

			result = resultList
		else:
			result = result2
        
        count = 0
        injured_list=[]

	#print result
	
        for temp in result :
            if count < temp['count']: 
	        injured_list=[]
                count =temp['count']
		injured_list.append(temp['injured'])
	    elif count == temp['count']: 
                #print "count", count
		injured_list.append(temp['injured'])
            else:
                break
        #print injured_list[random.randrange(0,len(injured_list))],injured_list
        return self.game.entry.getCharacter(injured_list[random.randrange(0,len(injured_list))])
    

class ConfidenceRule(BasicRule):
    min_players = 11
    max_players  = 16
    
    # �⺻ ����
    temp_truecharacter ={}
    temp_truecharacter[11] =  [1,1,1,1,16,3,4,17,17,6]
    temp_truecharacter[12] =  [1,1,1,1,1,16,3,4,17,17,6]
    temp_truecharacter[13] =  [1,1,1,1,1,1,16,3,4,17,17,6]
    temp_truecharacter[14] =  [1,1,1,1,1,16,3,4,17,17,17,6,12]
    temp_truecharacter[15] =  [1,1,1,1,1,1,16,3,4,17,17,17,6,12]
    temp_truecharacter[16] =  [1,1,1,1,1,1,1,16,3,4,17,17,17,6,12]    
    
    