<script lang="ts">
	import './layout.css';
	import favicon from '$lib/assets/favicon.svg';

	let { children } = $props();
</script>

<svelte:head><link rel="icon" href={favicon} /></svelte:head>

<p class="p-3"><span class="line-through">tinkletopia</span> homophobia.com</p>

{@render children()}
