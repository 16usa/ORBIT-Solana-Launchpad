use anchor_lang::prelude::*;
use anchor_lang::system_program;

// Replace with the actual deployed program ID before building/deploying.
declare_id!("11111111111111111111111111111111");

#[program]
pub mod orbit_smart_account {
    use super::*;

    pub fn initialize(ctx: Context<Initialize>) -> Result<()> {
        let vault = &mut ctx.accounts.vault;
        vault.owner = ctx.accounts.owner.key();
        vault.session_key = Pubkey::default();
        vault.session_expires_at = 0;
        vault.max_trade_lamports = 0;
        vault.remaining_budget_lamports = 0;
        vault.bump = ctx.bumps.vault;
        Ok(())
    }

    pub fn deposit(ctx: Context<Deposit>, lamports: u64) -> Result<()> {
        require!(lamports > 0, OrbitError::InvalidAmount);
        let cpi_accounts = system_program::Transfer {
            from: ctx.accounts.owner.to_account_info(),
            to: ctx.accounts.vault.to_account_info(),
        };
        system_program::transfer(CpiContext::new(ctx.accounts.system_program.to_account_info(), cpi_accounts), lamports)
    }

    pub fn withdraw(ctx: Context<Withdraw>, lamports: u64) -> Result<()> {
        require!(lamports > 0, OrbitError::InvalidAmount);
        let vault_info = ctx.accounts.vault.to_account_info();
        let rent_floor = Rent::get()?.minimum_balance(vault_info.data_len());
        let available = vault_info.lamports().checked_sub(rent_floor).ok_or(OrbitError::InsufficientFunds)?;
        require!(lamports <= available, OrbitError::InsufficientFunds);
        **vault_info.try_borrow_mut_lamports()? = vault_info.lamports().checked_sub(lamports).ok_or(OrbitError::ArithmeticOverflow)?;
        let owner_info = ctx.accounts.owner.to_account_info();
        **owner_info.try_borrow_mut_lamports()? = owner_info.lamports().checked_add(lamports).ok_or(OrbitError::ArithmeticOverflow)?;
        Ok(())
    }

    pub fn authorize_session(ctx: Context<ManageSession>, session_key: Pubkey, expires_at: i64, max_trade_lamports: u64, total_budget_lamports: u64) -> Result<()> {
        let now = Clock::get()?.unix_timestamp;
        require!(session_key != Pubkey::default(), OrbitError::InvalidSession);
        require!(expires_at > now && expires_at <= now.checked_add(86_400).ok_or(OrbitError::ArithmeticOverflow)?, OrbitError::InvalidExpiry);
        require!(max_trade_lamports > 0 && total_budget_lamports >= max_trade_lamports, OrbitError::InvalidAmount);
        let vault = &mut ctx.accounts.vault;
        vault.session_key = session_key;
        vault.session_expires_at = expires_at;
        vault.max_trade_lamports = max_trade_lamports;
        vault.remaining_budget_lamports = total_budget_lamports;
        Ok(())
    }

    pub fn revoke_session(ctx: Context<ManageSession>) -> Result<()> {
        let vault = &mut ctx.accounts.vault;
        vault.session_key = Pubkey::default();
        vault.session_expires_at = 0;
        vault.max_trade_lamports = 0;
        vault.remaining_budget_lamports = 0;
        Ok(())
    }
}

#[derive(Accounts)]
pub struct Initialize<'info> {
    #[account(mut)] pub owner: Signer<'info>,
    #[account(init, payer = owner, space = 8 + Vault::INIT_SPACE, seeds = [b"vault", owner.key().as_ref()], bump)]
    pub vault: Account<'info, Vault>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct Deposit<'info> {
    #[account(mut)] pub owner: Signer<'info>,
    #[account(mut, seeds = [b"vault", owner.key().as_ref()], bump = vault.bump, has_one = owner)]
    pub vault: Account<'info, Vault>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct Withdraw<'info> {
    #[account(mut)] pub owner: Signer<'info>,
    #[account(mut, seeds = [b"vault", owner.key().as_ref()], bump = vault.bump, has_one = owner)]
    pub vault: Account<'info, Vault>,
}

#[derive(Accounts)]
pub struct ManageSession<'info> {
    pub owner: Signer<'info>,
    #[account(mut, seeds = [b"vault", owner.key().as_ref()], bump = vault.bump, has_one = owner)]
    pub vault: Account<'info, Vault>,
}

#[account]
#[derive(InitSpace)]
pub struct Vault {
    pub owner: Pubkey,
    pub session_key: Pubkey,
    pub session_expires_at: i64,
    pub max_trade_lamports: u64,
    pub remaining_budget_lamports: u64,
    pub bump: u8,
}

#[error_code]
pub enum OrbitError {
    #[msg("Amount must be positive and limits must be valid")] InvalidAmount,
    #[msg("Not enough SOL above rent-exempt minimum")] InsufficientFunds,
    #[msg("Invalid session public key")] InvalidSession,
    #[msg("Session expiry must be within the next 24 hours")] InvalidExpiry,
    #[msg("Arithmetic overflow")] ArithmeticOverflow,
}
