from random import randint

from discord import Embed, Colour, Message, Member
from discord.ext import commands


command_prefix = '..'
object_id = 541


class TRPGCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot
        self.private_rooms: dict = {}
        
    @commands.Cog.listener()
    async def on_ready(self):
        print('ready.')
        
    @commands.Cog.listener()
    async def on_message(self, msg: Message):
        print(msg.author, msg.content)
        
    @commands.command(name='도움말', aliases=('도움', 'h', 'help'), brief=f'명령어의 도움말을 확인합니다.',
                      help='명령어의 도움말을 확인합니다.\n'
                           '사용법은 다음과 같습니다.\n'
                           '```\n'
                           f'{command_prefix}도움말 굴림\n'
                           f'{command_prefix}도움말 명령어\n'
                           f'{command_prefix}도움말 비밀방\n'
                           '```\n'
                           f'봇이 어떤 기능을 제공하는지 알고 싶다면 "{command_prefix}명령어" 명령어를 사용해보세요.')
    async def h(self, ctx: commands.Context, *tokens: str):
        cmd: commands.Bot = self.bot
        if tokens:
            for token in tokens:
                if isinstance(cmd, commands.Bot) or isinstance(cmd, commands.Group):
                    inner_cmd = cmd.get_command(token)
                else:
                    break
                cmd: commands.Command = inner_cmd
        else:
            cmd: commands.Command = self.h
        if cmd is None:
            await ctx.send(f'"{" ".join(tokens)}" 명령어를 찾을 수 없어!')
            return
        help_embed = Embed(title=f'**{self.bot.command_prefix}'
                           f'{cmd.full_parent_name + " " if cmd.full_parent_name else ""}{cmd.name}**',
                           description=cmd.brief, colour=Colour.blurple())
        help_embed.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)
        help_embed.set_thumbnail(url=self.bot.user.avatar_url)
        help_embed.add_field(name=':gear: 기능', value=cmd.help)
        if cmd.aliases:
            help_embed.add_field(name=':asterisk: 대체 가능한 단어', value=', '.join([f'"{a}"' for a in cmd.aliases]))
        if isinstance(cmd, commands.Group):
            value = '이 명령어는 다음의 하위 명령어를 포함하고 있습니다.\n```\n'
            for subcommand in cmd.commands:
                value += f'{self.bot.command_prefix}'
                value += f'{subcommand.full_parent_name + " " if subcommand.full_parent_name else ""}'
                value += f'{subcommand.name}\n'
            value += '```'
            help_embed.add_field(name=':diamond_shape_with_a_dot_inside: 하위 명령어', value=value)
        await ctx.send(embed=help_embed)

    @commands.command(name='명령어', aliases=('cmd', '커맨드', '커멘드'), brief='봇 명령어 목록을 조회합니다.',
                      help='봇이 제공하는 명령어들의 목록을 조회합니다.')
    async def cmd(self, ctx: commands.Context):
        cmds = [f'명령어 목록입니다.\n{"-" * 40}\n']
        for cmd in self.bot.commands:
            cmd_brief = f'║ **{self.bot.command_prefix}{f" {cmd.full_parent_name} " if cmd.full_parent_name else ""}'
            cmd_brief += f'{cmd.name}**\n║ -- *{cmd.brief}*\n\n'
            if len(cmds) == 1 and len(cmds[-1] + cmd_brief) > 2048:
                cmds.append(cmd_brief)
            elif len(cmds[-1] + cmd_brief) > 1024:
                cmds.append(cmd_brief)
            else:
                cmds[-1] += cmd_brief
        cmd_embed = Embed(title='명령어 목록', description=cmds.pop(0), colour=Colour.blurple())
        cmd_embed.set_thumbnail(url=self.bot.user.avatar_url)
        cmd_embed.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)
        embeds = [cmd_embed]
        for cmd_brief in cmds:
            embeds[-1].add_field(name='-', value=cmd_brief)
            if len(embeds[-1]) > 6000 or len(embeds[-1].fields) > 25:
                embeds[-1].remove_field(-1)
                embeds.append(Embed(colour=Colour.blurple()))
                embeds[-1].add_field(name='-', value=cmd_brief)
        for embed in embeds:
            await ctx.send(ctx.author.mention, embed=embed)
    
    @commands.command(name='굴림', aliases=('주사위', '굴리기', 'r', 'roll'), brief='주사위를 굴립니다.',
                      help='주사위를 굴립니다.\n'
                           '사용법은 다음과 같습니다.\n'
                           '```\n'
                           f'{command_prefix}굴림 D%\n'
                           f'{command_prefix}굴림 10D + 5\n'
                           f'{command_prefix}굴림 10 + 2D20 + 4 + 11 + 4D\n'
                           f'```\n'
                           f'굴림 기능은 덧셈을 지원하지만 뺄셈은 지원하지 않습니다.\n')
    async def r(self, ctx: commands.Context, *, roll: str):
        print('detected')
        parts = []
        if '+' in roll:
            for part in roll.split('+'):
                part.strip()
                if not part:
                    continue
                parts.append({'raw': part.strip().upper(), 'process': None, 'result': None})
        else:
            parts.append({'raw': roll.strip().upper(), 'process': None, 'result': None})
        print('parts', parts)
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
                print('throwns', throwns)
                part['process'] = f'[{" +".join(str(thrown) for thrown in throwns)}]'
                part['result'] = sum(throwns)
            else:
                part['process'] = part['raw']
                try:
                    part['result'] = int(part['raw'])
                except ValueError:
                    await ctx.send('더하는 값을 정확한 숫자로 입력해주세요.')
                    return
            print('part', parts)
        description = '**' + (" + ".join(part['raw'] for part in parts)) + '**'
        description += '\n= ' + " + ".join(part['process'] for part in parts)
        description += '\n= ***__' + str(sum(part['result'] for part in parts)) + '__***'
        embed = Embed(title=':game_die: 주사위 굴림', description=description, colour=Colour.blurple())
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)
        embed.set_thumbnail(url=self.bot.user.avatar_url)
        await ctx.send(ctx.author.mention, embed=embed)
        

bot = commands.Bot(command_prefix=command_prefix, help_command=None, case_insensitive=True)
bot.add_cog(TRPGCog(bot))

bot_token = ''
bot.run(bot_token)
