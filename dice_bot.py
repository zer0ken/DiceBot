from random import randint
from os import environ

from asyncio import sleep

from dbl.client import DBLClient
from decouple import config
from discord import Embed, Colour, Member, TextChannel, VoiceChannel, PermissionOverwrite
from discord.ext import commands

command_prefix = '>>'


class TRPGCog(commands.Cog):
    object_id = 115
    
    def __init__(self, client: commands.Bot):
        self.client: commands.Bot = client
        self.dbl_token = config('DBL_TOKEN')
        self.dblpy = DBLClient(client, self.dbl_token, autopost=True)
        
    @commands.command(name='초대링크', brief='봇을 초대하기 위한 링크를 확인합니다.',
                      help='봇을 서버에 초대하기 위해 필요한 링크를 확인합니다.')
    async def invite_link(self, ctx: commands.Context):
        url = 'https://discordbots.org/bot/609223331945906186'
        embed = Embed(title=':link: 봇 초대 링크', colour=Colour.blurple(),
                      description=f'봇을 다른 서버에 초대하려면 **[여기]({url})**를 클릭하세요.')
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)
        embed.set_thumbnail(url=self.client.user.avatar_url)
        await ctx.send(ctx.author.mention, embed=embed)
    
    @commands.command(name='도움말', aliases=('도움', 'h', 'help'), brief='명령어의 도움말을 확인합니다.',
                      help='명령어의 도움말을 확인합니다.\n'
                           '사용법은 다음과 같습니다.\n'
                           '```\n'
                           f'{command_prefix}도움말 굴림\n'
                           f'{command_prefix}도움말 명령어\n'
                           f'{command_prefix}도움말 개인방\n'
                           '```\n'
                           f'봇이 어떤 명령어를 제공하는지 알고 싶다면 "{command_prefix}명령어" 명령어를 사용해보세요.')
    async def help(self, ctx: commands.Context, *tokens: str):
        cmd: commands.Bot = self.client
        if tokens:
            for token in tokens:
                if isinstance(cmd, commands.Bot) or isinstance(cmd, commands.Group):
                    inner_cmd = cmd.get_command(token)
                else:
                    break
                cmd: commands.Command = inner_cmd
        else:
            cmd: commands.Command = self.help
        if cmd is None:
            await ctx.send(f'"{" ".join(tokens)}" 명령어를 찾을 수 없습니다.')
            return
        help_embed = Embed(title=f'**{self.client.command_prefix}'
                                 f'{cmd.full_parent_name + " " if cmd.full_parent_name else ""}{cmd.name}**',
                           description=cmd.brief, colour=Colour.blurple())
        help_embed.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)
        help_embed.set_thumbnail(url=self.client.user.avatar_url)
        help_embed.add_field(name=':gear: 기능', value=cmd.help, inline=False)
        if cmd.aliases:
            help_embed.add_field(name=':asterisk: 대체 가능한 단어', value=', '.join([f'"{a}"' for a in cmd.aliases]),
                                 inline=False)
        if isinstance(cmd, commands.Group):
            value = '이 명령어는 다음의 하위 명령어를 포함하고 있습니다.\n```\n'
            for subcommand in cmd.commands:
                value += f'{self.client.command_prefix}'
                value += f'{subcommand.full_parent_name + " " if subcommand.full_parent_name else ""}'
                value += f'{subcommand.name}\n'
            value += '```'
            help_embed.add_field(name=':diamond_shape_with_a_dot_inside: 하위 명령어', value=value, inline=False)
        await ctx.send(embed=help_embed)
    
    @commands.command(name='명령어', aliases=('cmd', '커맨드', '커멘드', 'cmds'), brief='봇 명령어 목록을 조회합니다.',
                      help='봇이 제공하는 명령어들의 목록을 조회합니다.')
    async def cmd(self, ctx: commands.Context):
        cmds = [f'명령어 목록입니다.\n{"-" * 40}\n']
        for cmd in self.client.commands:
            cmd_brief = f'**{self.client.command_prefix}{f" {cmd.full_parent_name} " if cmd.full_parent_name else ""}'
            cmd_brief += f'{cmd.name}**\n-- *{cmd.brief}*\n\n'
            if len(cmds) == 1 and len(cmds[-1] + cmd_brief) > 2048:
                cmds.append(cmd_brief)
            elif len(cmds[-1] + cmd_brief) > 1024:
                cmds.append(cmd_brief)
            else:
                cmds[-1] += cmd_brief
        cmd_embed = Embed(title='명령어 목록', description=cmds.pop(0), colour=Colour.blurple())
        cmd_embed.set_thumbnail(url=self.client.user.avatar_url)
        cmd_embed.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)
        embeds = [cmd_embed]
        for cmd_brief in cmds:
            embeds[-1].add_field(name='-', value=cmd_brief, inline=False)
            if len(embeds[-1]) > 6000 or len(embeds[-1].fields) > 25:
                embeds[-1].remove_field(-1)
                embeds.append(Embed(colour=Colour.blurple()))
                embeds[-1].add_field(name='-', value=cmd_brief)
        for embed in embeds:
            await ctx.send(ctx.author.mention, embed=embed)
    
    @commands.command(name='굴림', aliases=('주사위', '굴리기', 'r', 'roll', '굴'), brief='주사위를 굴립니다.',
                      help='주사위를 굴립니다.\n'
                           '사용법은 다음과 같습니다.\n'
                           '```\n'
                           '[육면체 주사위 굴림]\n'
                           f'{command_prefix}굴림\n\n'
                           '[복잡한 주사위 굴림]\n'
                           f'{command_prefix}굴림 D%\n'
                           f'{command_prefix}굴림 10D + 5\n'
                           f'{command_prefix}굴림 10 + 2D20 + 4 - 11 - 4D\n'
                           '```')
    async def roll(self, ctx: commands.Context, *, roll: str = 'D'):
        parts = []
        if '+' in roll or '-' in roll:
            for part in roll.split('+'):
                if not part.strip():
                    continue
                if '-' in roll:
                    for i in range(len(part.split('-'))):
                        parts_ = part.split('-')
                        if not parts_[i].strip():
                            continue
                        part_dict = {'raw': parts_[i].strip().upper(), 'sign': '-', 'process': None, 'result': None}
                        if i:
                            part_dict['sign'] = '-'
                        else:
                            part_dict['sign'] = '+'
                        parts.append(part_dict)
                else:
                    parts.append({'raw': part.strip().upper(), 'sign': '+', 'process': None, 'result': None})
        else:
            parts.append({'raw': roll.strip().upper(), 'sign': '+', 'process': None, 'result': None})
        for part in parts:
            part['raw'] = part['raw'].replace(' ', '', part['raw'].count(' '))
            if 'D' in part['raw']:
                raws = part['raw'].split('D')
                try:
                    dices = int(raws[0].strip() if raws[0] else 1)
                    pips = int((raws[1].strip() if raws[1] != '%' else '100') if raws[1] else 6)
                except ValueError:
                    await ctx.send('주사위 수와 눈을 정확한 숫자로 입력해주세요.')
                    return
                if dices <= 0:
                    await ctx.send('주사위의 수는 한 개 이상이어야 합니다.')
                    return
                if pips <= 0:
                    await ctx.send('주사위의 눈은 한 개 이상이어야 합니다.')
                    return
                throwns = []
                for i in range(dices):
                    throwns.append(randint(1, pips))
                part['process'] = str(throwns)
                part['result'] = sum(throwns) * (-1 if part['sign'] == '-' else 1)
            else:
                part['process'] = part['raw']
                try:
                    part['result'] = int(part['raw']) * (-1 if part['sign'] == '-' else 1)
                except ValueError:
                    await ctx.send('더하는 값을 정확한 숫자로 입력해주세요.')
                    return
        raw_description = ''
        process_description = ''
        for part in parts:
            raw_description += f'{part["sign"]} {part["raw"]} '
            process_description += f'{part["sign"]} {part["process"]} '
        description = '**' + raw_description + '**'
        description += '\n= ' + process_description
        description += '\n= ***__' + str(sum(part['result'] for part in parts)) + '__***'
        embed = Embed(title=':game_die: 주사위 굴림', description=description, colour=Colour.blurple())
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)
        embed.set_thumbnail(url=self.client.user.avatar_url)
        await ctx.send(ctx.author.mention, embed=embed)
    
    @commands.command(name='개인방', aliases=('pc', 'pr', 'private', '비밀방'),
                      brief='개인방을 만듭니다.',
                      help='특정 멤버만 볼 수 있는 텍스트/음성 채널을 만듭니다.\n'
                           '사용법은 다음과 같습니다.\n'
                           '```\n'
                           f'{command_prefix}개인방 @userName#1234\n'
                           f'{command_prefix}개인방 userName\n'
                           f'{command_prefix}개인방 @secondUser#5678 @andThird#9012 @fourth#3456\n'
                           f'{command_prefix}개인방 secondUser andThird fourth'
                           '```\n'
                           ' 참여하는 멤버를 `@이름#0000`와 같이 언급할 수 없다면 '
                           '`이름`과 같이 이름만 입력해도 됩니다.')
    async def private_room(self, ctx: commands.Context, member: Member, *members: Member):
        msg = await ctx.send(f'{ctx.author.mention} 개인방을 만들고 있습니다...')
        try:
            overwrites = {ctx.guild.default_role: PermissionOverwrite(read_messages=False),
                          self.client.user: PermissionOverwrite(read_messages=True)}
            members = list(members)
            members.append(member)
            for member in members:
                overwrites[member] = PermissionOverwrite(read_messages=True)
            text_channel: TextChannel = await ctx.guild.create_text_channel(f'개인방 {self.object_id}호실',
                                                                            overwrites=overwrites)
            voice_channel: VoiceChannel = await ctx.guild.create_voice_channel(f'개인방 {self.object_id}호실',
                                                                               overwrites=overwrites)
            text_url = f'https://discordapp.com/channels/{ctx.guild.id}/{text_channel.id}'
            voice_url = f'https://discordapp.com/channels/{ctx.guild.id}/{voice_channel.id}'
            embed = Embed(title=':spy: 개인방 개설', colour=Colour.blurple(), description='개인방을 개설했습니다.')
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)
            embed.set_thumbnail(url=ctx.guild.icon_url)
            embed.add_field(name=':busts_in_silhouette: 멤버', inline=False,
                            value=f':small_orange_diamond: {ctx.author}\n:small_blue_diamond: ' +
                                  ('\n:small_blue_diamond: '.join(str(member) for member in members)))
            embed.add_field(name=':envelope: 텍스트 채널', value=f'텍스트 채널을 보려면 **[여기]({text_url})**를 클릭하세요.')
            embed.add_field(name=':loud_sound: 음성 채널 (화면공유)',
                            value=f'음성 채널에서 화면공유를 활성화하려면 **[여기]({voice_url})**를 클릭하세요.')
            await msg.edit(content=f'{ctx.author.mention} 개인방을 만들었습니다.', embed=embed)
            await text_channel.send(embed=embed)
            self.object_id += 1
        except BaseException as e:
            await msg.edit(content=f'개인방을 만들 수 없습니다...```\n{e}\n```')


bot = commands.Bot(command_prefix=command_prefix, help_command=None, case_insensitive=True)
bot.add_cog(TRPGCog(bot))
bot.add_cog(DiscordBotsOrgAPI(bot))

bot_token = config("BOT_TOKEN")
bot.run(bot_token)
