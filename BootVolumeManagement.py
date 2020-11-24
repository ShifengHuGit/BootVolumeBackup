import click
import io
import json
import time
import oci
import os
from oci import config

Default_CompartmentID = ""
Default_Region = ""


@click.group()
@click.option('--config-file', '-c', default='~/.oci/config',
              help='Use alternative config file (default ~/.oci/config).')
@click.option('--profile', '-p', default='default',
              help='Use alternative Profile  file (default [default]).')
@click.pass_context
def main(ctx, config_file, profile):
    user_config = config.from_file(file_location=config_file, profile_name=profile)
    global Default_CompartmentID,Default_Region
    if "compartment_id" in user_config:
        Default_CompartmentID = user_config["compartment_id"]
    else:
        click.echo('>>> Error: No compartment_id found at : %s, with Profile: %s' % (config_file, profile))
        click.echo('>>> Error: Before use any sub-command, your need to update your config file with compartment_id.')
        exit(0)
    Default_Region = user_config["region"]
    #print(Default_CompartmentID)
    #print(Default_Region)
    ctx.obj = user_config
    click.echo(click.style('▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄[ Backup Management Started ]▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄', fg='yellow', bg='black',bold=True))
    click.echo('█\n█ → Using the Configuration file: %s, and Profile: %s' % (config_file, profile))
    click.echo('█'+click.style('-------------------------------------------------', fg='yellow'))



@main.command()
@click.option('--bootvolumeid', '-I',
                help='Filter to display the boot volume backup via the bootVolume ID. if not set, return all backups.')
@click.option('--compartmentid', '-C', 
                default=lambda:  Default_CompartmentID,
                required = True,
                help='Your compartmentID that the resource belongs to. if not set , using the CompartmentID from config file.')
@click.option('--region','-R',
                default=lambda: Default_Region,
                prompt='Region for display',
                required = True,
                type=click.Choice(['ap-osaka-1', 'ap-tokyo-1']),
                help='The region that resource belongs to. If not set, using the Region from config file. Only support to [ap-osaka-1, ap-tokyo-1].')
@click.pass_context
def ListBackup(ctx,bootvolumeid, compartmentid, region):
    click.echo('█ → List the bootVolume\'s %s backup.' % bootvolumeid)
    click.echo('█ → under the Compartment: %s .' % compartmentid)
    click.echo('█ → at the Region: %s .' % region)
    click.echo('█'+click.style('-------------------------------------------------', fg='yellow'))
    user_config = ctx.obj
    user_config["region"] = region
    #print(str(user_config))
    #print("the Comp ID: " + compartmentid)
    #print("the Region : " + region)
    if(id):
        ListBootVolumeBackup(compartmentid, user_config, boot_volume_id=bootvolumeid)
    else:
        ListBootVolumeBackup(compartmentid, user_config)
    click.echo(click.style('▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀[ Backup Management Ended ]▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀',fg='yellow', bg='black'))



@main.command()
@click.option('--region','-R',
                default=lambda: Default_Region,
                type=click.Choice(['ap-osaka-1', 'ap-tokyo-1']),
                help='The region that resource belongs to. If not set, using the Region from config file. Only support to [ap-osaka-1, ap-tokyo-1].')
@click.option('--backupid', '-I',
                required = True,
                help='The bootvolumebackupid that you want to copy to remote side')
@click.option('--copyto','-T', prompt='Destination Region',
                required = True,
                type=click.Choice(['ap-osaka-1', 'ap-tokyo-1']), 
                help='The destination region that you want to copy to. Only support to [ap-osaka-1, ap-tokyo-1].')
@click.option('--name','-N', prompt='Display Name at remote side', 
                default='RemoteCopyBackup', 
                help='The backup name displayed at remote side.')
#@click.option('--delete','-D', prompt='Do you want to delete the source backup after copy finished', 
#                default='No',type=click.Choice(['Yes', 'No']), 
#                help='wherther delete the source backup , Type yes to delete the source backup after copy, Default is No.')
@click.pass_context
def CopyBackup(ctx, region,backupid, copyto, name):
    config = ctx.obj
    result = oci.audit.models.Response()
    click.echo('█ → Copying  backup with ID: %s .' % backupid)
    click.echo('█ → from   :  %s .' % region)
    click.echo('█ → To     :  %s .' % copyto)
    click.echo('█ → using display name: %s .' % name)
    click.echo('█'+click.style('-------------------------------------------------', fg='yellow'))
    Volume = oci.core.BlockstorageClient(config)
    try:
        result = Volume.copy_boot_volume_backup(
                backupid,
                oci.core.models.CopyBootVolumeBackupDetails(
                    destination_region=copyto,
                    display_name=name
                )   
        )
        click.echo('█  ← HTTP Code: %d' % result.status)
        click.echo('█  ← The time of Copying backup depends on the backup size ')
        click.echo('█  ← Please check the remote side of the copy progress from OCI console')
        click.echo('█  ← or use this command [listbackup -R [region] -I [bootvolumeid] ]')
        Mapping = json.loads(str(result.data))
        click.echo("█\n█ ================Backup:{display_name}=================\n" 
                "█ ← id:    {id}\n"
                "█ ← status: {lifecycle_state}\n"
                "█ ← compartmentId: {compartment_id}\n"
                "█ ← Backupsize(GB): {unique_size_in_gbs}/{size_in_gbs}\n"
                "█ ← type: {type}\n"
                "█ ← CreateAt: {time_created}\n"
                "█ ← expirationTime: {expiration_time}\n"
                "█ ===========================================================\n"
                "".format(**Mapping))
        click.echo(click.style('▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀[ Backup Management Ended ]▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀',fg='yellow', bg='black'))
    
    except oci.exceptions.ServiceError as e:
        if e.status == 404:
            click.echo('█ ← Error Http Code:'+click.style('  %d' % e.status, fg='red',bold=True))
            click.echo('█ ← Error Http Msg:'+click.style('  %s' % e.message, fg='red',bold=True))
            click.echo('█ ← '+click.style(' You may use incorrect resource ID or compartmentID?' , fg='red',bold=True))
            click.echo('█ ← '+click.style(' Or Resource has been deleted.' , fg='red',bold=True))
            click.echo(click.style('▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀[ Backup Management Ended ]▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀',fg='yellow', bg='black',bold=True))
        else:
            print(e)
        os._exit(0)


@main.command()
@click.option('--bootvolumebackupid', '-I',
                help='The BootVolume backup ID that you want to delete')
@click.option('--region','-R',
                required=True,
                prompt='Region to delete',
                type=click.Choice(['ap-osaka-1', 'ap-tokyo-1']),
                help='The region that that has backup file. Must input before delete it. Only support to [ap-osaka-1, ap-tokyo-1].')
@click.pass_context
def DeleteBackup(ctx, bootvolumebackupid, region):
    config = ctx.obj
    click.echo('█ → Delete backup with ID: %s .' % bootvolumebackupid)
    click.echo('█ → at region   :  %s .' % region)
    click.echo('█'+click.style('-------------------------------------------------', fg='yellow'))
    config["region"] = region
    try:
        Volume = oci.core.BlockstorageClient(config)
        result = Volume.delete_boot_volume_backup(
                bootvolumebackupid
        )
        click.echo('█  ← HTTP Code: %d' % result.status)
        click.echo('█  ← Delete Request has sent to OCI')
        click.echo(click.style('▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀[ Backup Management Ended ]▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀',fg='yellow', bg='black'))
    
    except oci.exceptions.ServiceError as e:
        if e.status == 404 or 400:
            click.echo('█ ← Error Http Code:'+click.style('  %d' % e.status, fg='red',bold=True))
            click.echo('█ ← Error Http Msg:'+click.style('  %s' % e.message, fg='red',bold=True))
            click.echo('█ ← '+click.style(' You may use incorrect resource ID or compartmentID?' , fg='red',bold=True))
            click.echo('█ ← '+click.style(' Or Resource has been deleted.' , fg='red',bold=True))
            click.echo(click.style('▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀[ Backup Management Ended ]▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀',fg='yellow', bg='black',bold=True))
        else:
            print(e)
        os._exit(0)   

def ListBootVolumeBackup(compartmentid, config, **kwargs):
    Volume = oci.core.BlockstorageClient(config)

    try:
        BootVolumeList = Volume.list_boot_volume_backups(compartmentid, **kwargs)
        for BootV in BootVolumeList.data:
            #print (str(BootV))
            Mapping = json.loads(str(BootV))
            click.echo("█ ▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪◇◇▶ Backup:{display_name} ◀◇◇▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪\n" 
                "█ ← id:    {id}\n"
                "█ ← status: {lifecycle_state}\n"
                "█ ← compartmentId: {compartment_id}\n"
                "█ ← Backupsize(GB): {unique_size_in_gbs}/{size_in_gbs}\n"
                "█ ← type: {type}\n"
                "█ ← CreateAt: {time_created}\n"
                "█ ← expirationTime: {expiration_time}\n"
                "█ ▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪▪\n"
                "".format(**Mapping))
    except oci.exceptions.ServiceError as e:
        if e.status == 404 or 400:
            click.echo('█ ← Error Http Code:'+click.style('  %d' % e.status, fg='red',bold=True))
            click.echo('█ ← Error Http Msg:'+click.style('  %s' % e.message, fg='red',bold=True))
            click.echo('█ ← '+click.style(' You may use incorrect resource ID or compartmentID?' , fg='red',bold=True))
            click.echo('█ ← '+click.style(' Or Resource has been deleted.' , fg='red',bold=True))
            click.echo(click.style('▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀[ Backup Management Ended ]▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀',fg='yellow', bg='black',bold=True))
        else:
            print(e)
        os._exit(0)   

if __name__ == '__main__':
    main()
